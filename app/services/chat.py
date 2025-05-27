import uuid
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any

from cassandra.util import uuid_from_time
from cassandra.query import SimpleStatement
from cassandra import ConsistencyLevel

from app.db.cassandra import session
from app.services.user import fetch_member_info

from app.schemas.data_validators import SendChatMessageValidator
from app.schemas.data_classes import RoomDetailsParams

from app.utils.logger import get_logger

logger = get_logger('chat')

async def create_or_get_chat_room(team_id: str, user1_id: str, user2_id: str, cookies: Dict) -> str:
    try:
        users = sorted([user1_id, user2_id])
        room_id = f'room_{team_id}_{users[0]}_{users[1]}'
        applied = session.execute(
            """
            INSERT INTO chat_rooms (team_id, room_id, user1_id, user2_id, created_at)
            VALUES (%s, %s, %s, %s, %s)
            IF NOT EXISTS
            """, 
            (team_id, room_id, users[0], users[1], datetime.now(timezone.utc))
        ).was_applied

        if applied:
            resp = await fetch_member_info(team_id, user2_id, cookies)
            if not resp:
                raise ValueError(
                    'Could not verify participant team membership (user_id, {user2_id})'
                )
            
            # Insert the room mapping for both users
            for user_id, participant_id in [(users[0], users[1]), (users[1], users[0])]:
                asyncio.to_thread(session.execute,
                    """
                    INSERT INTO user_chats_by_user (
                        team_id, room_id, user_id, participant_id, created_at
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    """, (
                        team_id, 
                        room_id, 
                        user_id, 
                        participant_id, 
                        datetime.now(timezone.utc)
                    )
                )

        return room_id
    except ValueError as ve:
        logger.exception(ve)
        raise
    except Exception as e:
        logger.exception(f"Unexpected error in create_or_get_chat_room({user1_id}, {user2_id}): {e}")
        raise


async def get_user_rooms(team_id: str, user_id: str, cookies: dict, room_id=None):
    query = """
        SELECT room_id, participant_id, last_message, last_message_type, created_at 
        FROM user_chats_by_user WHERE team_id = %s AND user_id = %s
    """
    params = [team_id, user_id]

    if room_id:
        query += ' AND room_id = %s'
        params.append(room_id)
    
    rows = await asyncio.to_thread(session.execute, query, params)
    
    async with asyncio.TaskGroup() as tg:
        tasks = [
            tg.create_task(
                get_room_details(RoomDetailsParams.from_row(row, team_id, user_id, cookies))
            )
            for row in rows
        ]
    rooms = [t.result() for t in tasks]
    return rooms


async def get_room_details(params: RoomDetailsParams) -> Dict[str, Any]:
    try:
        async with asyncio.TaskGroup() as tg:
            participant_info_task = tg.create_task(
                fetch_member_info(params.team_id, params.participant_id, params.cookies)
            )
            unread_count_task = tg.create_task(
                get_unread_messages_count(params.team_id, params.room_id, params.user_id)
            )
        
        participant_info = participant_info_task.result()
        unread_count = unread_count_task.result()
        
        if not participant_info or not isinstance(participant_info, list):
            raise ValueError('Participant info not found or invalid format')
        
        participant = participant_info[0]
        
        return {
            'room_id': params.room_id,
            'participant_id': params.participant_id,
            'participant_name': participant['display_name'],
            'is_participant_online': participant.get('online', False),
            'participant_profile_pic': participant.get('profile_picture_url', ''),
            'last_message': params.last_message,
            'last_message_type': params.last_message_type,
            'unread_messages_count': unread_count if unread_count is not None else 0,
            'created_at': params.created_at.isoformat(),
        }

    except ValueError as ve:
        logger.exception(f'Validation error: {ve}')
        raise
    except Exception as e:
        logger.exception(f'Unexpected error in get_room_details: {e}')
        raise


async def get_unread_messages_count(team_id: str, room_id: str, user_id: str) -> int:
    last_read = await asyncio.to_thread(
        lambda: session.execute(
            """
            SELECT last_read FROM user_chats_by_user WHERE
            team_id = %s AND room_id = %s AND user_id = %s
            """, (team_id, room_id, user_id)
        ).one()
    )

    if not last_read or not last_read.last_read:
        last_read_time = datetime.min
    else:
        last_read_time = last_read.last_read

    last_read_uuid = uuid_from_time(last_read_time)
    count_row = await asyncio.to_thread(
        lambda: session.execute(
            """
            SELECT COUNT(*) FROM direct_messages
            WHERE room_id = %s AND message_id > %s
            """,
            (room_id, last_read_uuid)
        ).one()
    )

    return count_row.count if count_row else 0
    

async def handle_direct_text_message(user_id, data: SendChatMessageValidator):
    try:
        message_id = uuid.uuid1()
        timestamp = datetime.now(timezone.utc)
        room_id = data.room_id
        receiver_id = data.receiver_id
        content = data.content
        message_type = data.message_type

        insert_stmt = SimpleStatement(
            """
            INSERT INTO direct_messages (
                room_id, message_id, sender_id, receiver_id, 
                message_type, content, timestamp
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, consistency_level=ConsistencyLevel.QUORUM)
        
        update_stmt = """
            UPDATE user_chats_by_user
            SET last_message = %s, last_message_type = %s, last_message_timestamp = %s
            WHERE user_id = %s AND room_id = %s
        """
        
        async with asyncio.TaskGroup() as tg:
            tg.create_task(asyncio.to_thread(
                session.execute,
                insert_stmt,
                (room_id, message_id, user_id, receiver_id, message_type, content, timestamp)
            ))

            for uid in (user_id, receiver_id):
                tg.create_task(asyncio.to_thread(
                    session.execute,
                    update_stmt,
                    (content, message_type, timestamp, uid, room_id)
                ))

        return {
            'room_id': room_id,
            'message_id': str(message_id),
            'sender_id': user_id,
            'receiver_id': receiver_id,
            'content': content,
            'message_type': message_type,
            'timestamp': timestamp.isoformat(timespec='seconds')
        }
    except Exception as e:
        logger.exception('Error in handle_direct_text_message')
        raise
