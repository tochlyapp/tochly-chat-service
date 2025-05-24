import asyncio
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Request, Query, HTTPException, status

from app.db.cassandra import session
from app.services.chat import get_user_rooms
from app.utils.auth import verify_cookies

router = APIRouter()

@router.get('/api/chats/rooms')
async def get_user_chat_rooms(
    request: Request,
    team_id: str,
    user_id: str,
    search: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    skip: int = Query(0, ge=0),
):
    try:
        cookies = request.cookies
        await verify_cookies(cookies)
        rooms = await get_user_rooms(team_id=team_id, user_id=user_id, cookies=cookies)
        
        if search:
            search_lower = search.lower()
            rooms = [
                r for r in rooms if
                search_lower in (r['participant_name'] or '').lower()
                or search_lower in (r['last_message'] or '').lower()
            ]

        paginated_rooms = rooms[skip:skip+limit]
        return paginated_rooms
    except HTTPException as e:
        raise e
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=str(e)
        )
    except Exception as ee:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail='Internal Server Error'
        )

@router.get('/api/chats/rooms/{room_id}/messages')
async def get_room_messages(
    request: Request,
    team_id: str,
    room_id: str,
    user_id: str = Query(..., description='ID of the user requesting messages'),
    search: Optional[str] = Query(None),
    before: Optional[datetime] = Query(None, description='Fetch messages before this timestamp'),
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0),
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
                (team_id, room_id, user_id)
            ).one()
        )

        if not room_exist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail='Room does not exist'
            )
        
        query = """
            SELECT (
                message_id, sender_id, receiver_id, content, 
                message_type, attachment_url, file_name. file_size, mime_type, timestamp
            )
            FROM direct_messages
            WHERE room_id = %s
        """
        params = [room_id]

        if before:
            query += ' AND timestamp < %s'
            params.append(before)

        query += ' ORDER BY message_id ASC'
        rows = await asyncio.to_thread(session.execute, query, params)

        messages = []

        for row in rows:
            message_data = {
                'message_id': str(row.message_id),
                'sender_id': str(row.sender_id),
                'message': row.message,
                'timestamp': row.timestamp.isoformat()
            }

            if not search or (search.lower() in row.message.lower()):
                messages.append(message_data)
        
        paginated_messages = messages[skip:skip+limit]

        return {
            'room_id': room_id,
            'messages': paginated_messages,
            'count': len(paginated_messages),
            'total': len(messages),
            'has_more': len(messages) > (skip + limit)
        }
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail='Internal Server Error'
        )
