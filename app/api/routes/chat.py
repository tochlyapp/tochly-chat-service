import asyncio
from fastapi import (
    APIRouter, 
    Request, 
    HTTPException, 
    status, 
    Depends
)

from app.db.cassandra import get_cassandra_session
from app.services.chat import get_user_rooms
from app.utils.auth import verify_cookies
from app.schemas.data_validators import QueryParams, RoomMessagesQueryParams

router = APIRouter()
session = get_cassandra_session()

@router.get('/api/chats/rooms')
async def get_user_chat_rooms(
    request: Request, 
    params: QueryParams = Depends()
):
    try:
        cookies = request.cookies
        await verify_cookies(cookies)
        rooms = await get_user_rooms(
            team_id=params.team_id, 
            user_id=params.user_id, 
            cookies=cookies
        )
        
        if params.search:
            search_lower = params.search.lower()
            rooms = [
                r for r in rooms if
                search_lower in (r['participant_name'] or '').lower()
                or search_lower in (r['last_message'] or '').lower()
            ]

        paginated_rooms = rooms[params.skip:params.skip+params.limit]
        return paginated_rooms
    except HTTPException as e:
        raise e
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=str(e)
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail='Internal Server Error'
        )

@router.get('/api/chats/rooms/{room_id}/messages')
async def get_room_messages(
    request: Request, 
    params: RoomMessagesQueryParams = Depends()
):
    try:
        cookies = request.cookies
        await verify_cookies(cookies)
                
        room_exist = await asyncio.to_thread(
            lambda: session.execute(
                """
                SELECT room_id FROM user_chats_by_user 
                WHERE team_id = %s AND room_id = %s AND user_id = %s LIMIT 1
                """, 
                (params.team_id, params.room_id, params.user_id)
            ).one()
        )

        if not room_exist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail='Room does not exist'
            )
        
        query = """
            SELECT message_id, sender_id, receiver_id, 
                content, message_type, attachment_url, 
                file_name, file_size, mime_type, timestamp
            FROM direct_messages
            WHERE room_id = %s
        """
        query_params = [params.room_id]

        if params.before:
            query += ' AND timestamp < %s'
            query_params.append(params.before)

        query += ' ORDER BY message_id ASC'
        rows = await asyncio.to_thread(session.execute, query, query_params)

        messages = []

        for row in rows:
            message_data = {
                'message_id': str(row.message_id),
                'sender_id': str(row.sender_id),
                'content': row.content,
                'timestamp': row.timestamp.isoformat()
            }

            if not params.search or (params.search.lower() in (row.content or '').lower()):
                messages.append(message_data)
        
        paginated_messages = messages[params.skip:params.skip+params.limit]

        return {
            'room_id': params.room_id,
            'messages': paginated_messages,
            'count': len(paginated_messages),
            'total': len(messages),
            'has_more': len(messages) > (params.skip + params.limit)
        }
    except HTTPException as e:
        raise e
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=str(e)
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail='Internal Server Error'
        )
