import asyncio
from datetime import datetime, timezone
from http.cookies import SimpleCookie
from fastapi import HTTPException

from app.db.cassandra import session

from app.utils.jwt_utils import decode_jwt
from app.utils.auth import verify_cookies

from app.sio_server import sio
from app.services.chat import (
    create_or_get_chat_room,
    get_user_rooms,
    handle_direct_text_message,
)

from app.schemas.data_validators import (
    StartChatValidator, 
    SendChatMessageValidator
)

connected_cookies = {}

@sio.event
async def connect(sid, environ):
    cookies = SimpleCookie()
    cookies.load(environ.get('HTTP_COOKIE', ''))

    try:
        await verify_cookies(cookies)
    except HTTPException:
        print('HEREEEEEEEEEE')
        await sio.emit(
            'auth_failed', 
            {'message': 'Authentication failed. Disconnecting...'},
            room=sid,
        )
        await sio.disconnect(sid)
        return
            
    token = cookies.get('access')
    if not token:
        await sio.emit('auth_failed', {'message': 'Missing token'}, room=sid)
        await sio.disconnect(sid)
        return

    decoded = decode_jwt(token.value)
    if not decoded:
        await sio.emit('auth_failed', {'message': 'Invalid token'}, room=sid)
        await sio.disconnect(sid)
        return

    user_id = decoded.get('user_id')
    if not user_id:
        await sio.emit('auth_failed', {'message': 'Invalid payload'}, room=sid)
        await sio.disconnect(sid)
        return

    connected_cookies[sid] = cookies
    await sio.save_session(sid, {'user_id': str(user_id)})
    print(f'Client {sid} connected')


@sio.event
async def start_chat(sid, data):
    print('==================================')
    try:
        sio_session = await sio.get_session(sid)
        user_id = sio_session.get('user_id') if sio_session else None

        if not user_id:
            await sio.emit('auth_failed', {
                'message': 'Unauthorized',
                'code': 401
            }, room=sid)
            return
        
        validated_data = StartChatValidator(**data)
        team_id = validated_data.team_id
        receiver_id = validated_data.receiver_id
        
        cookies = connected_cookies.get(sid, {})
        room_id = await create_or_get_chat_room(
            team_id,
            user_id, 
            receiver_id,
            cookies,
        )
        sio.enter_room(sid, room_id)

        room_details = await get_user_rooms(
            team_id=team_id,
            user_id=user_id,
            cookies=cookies,
            room_id=room_id,
        )
        await sio.emit('chat_room', {
            'status': 'success',
            'data': room_details[0],
        }, room=sid)

        await asyncio.to_thread(session.execute,
            """
            UPDATE user_chats_by_user
            SET last_read = %s
            WHERE user_id = %s AND room_id = %s AND team_id = %s
            """, (datetime.now(timezone.utc), user_id, room_id, team_id)
        )
    except ValueError as ve:
        print('Error400', ve)
        await sio.emit('error', {
            'message': str(ve),
            'code': 400
        }, room=sid)
    except Exception as e:
        print('Error500', e)
        await sio.emit('error', {
            'message': 'Internal server error',
            'code': 500,
            'debug': str(e)
        }, room=sid)

@sio.event
async def send_direct_message(sid, data):
    try:
        sio_session = await sio.get_session(sid)
        user_id = sio_session.get('user_id') if sio_session else None

        if not user_id:
            await sio.emit('auth_failed', {
                'message': 'Unauthorized',
                'code': 401
            }, room=sid)
            return
        
        validated_data = SendChatMessageValidator(**data)
        room_id = validated_data.room_id
        message_type = validated_data.message_type

        if message_type == 'text':
            message_data = await handle_direct_text_message(user_id, validated_data)
        else:
            # handle messages containing file
            message_data = {} # To be implemented

        await sio.emit(
            'new_message',
            message_data,
            room=room_id,
        )
    except ValueError as ve:
        print(f'Error sending message: {ve}')
        await sio.emit('error', {
            'message': str(ve),
            'code': 400
        }, room=sid)
    except Exception as e:
        print(f'Error sending message: {e}')
        await sio.emit('error', {'message': 'Failed to send message.'}, to=sid)

@sio.event
async def disconnect(sid):
    connected_cookies.pop(sid, None)
    print(f'Client disconnected: {sid}')
