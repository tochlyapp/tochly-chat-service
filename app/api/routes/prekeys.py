from uuid import UUID

from fastapi import (
    APIRouter, 
    HTTPException, 
    status, 
    Path,
)

from app.db.cassandra import get_cassandra_session
from app.schemas.models.prekey import PrekeyBundle

router = APIRouter()
session = get_cassandra_session()

user_id_validation = Path(
    ..., 
    min_length=1,
    max_length=10, 
    pattern=r'^[0-9]+$'
),

@router.get('/api/prekeys/exists/{user_id}/{device_id}')
async def check_prekey_bundle_exists(
    user_id: str = user_id_validation,
    device_id: UUID = Path(...),
):
    try:
        row = session.execute(
            '''
            SELECT user_id FROM prekeys_by_user_device
            WHERE user_id = %s AND device_id = %s
            ''',
            (user_id, device_id)
        ).one()

        return {'exists': bool(row)}
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail='Internal Server Error'
        )

@router.get('/api/prekeys/{user_id}/{device_id}', response_model=PrekeyBundle)
async def get_or_create_prekey_bundle(
    user_id: str = user_id_validation,
    device_id: UUID = Path(...),
):
    try:
        row = session.execute(
            '''
            SELECT * FROM prekeys_by_user_device
            WHERE user_id = %s AND device_id = %s
            ''',
            (user_id, device_id)
        ).one()

        if not row:
            raise HTTPException(
                status_code=404, 
                detail='No prekey bundle found — client should generate one.'
            )

        one_time_row = session.execute(
            '''
            SELECT prekey_id, prekey FROM one_time_prekeys_by_user_device
            WHERE user_id = %s AND device_id = %s AND used = false LIMIT 1
            ''',
            (user_id, device_id)
        ).one()

        if not one_time_row:
            raise HTTPException(
                status_code=410, 
                detail='No available one-time prekeys'
            )

        session.execute(
            '''
            UPDATE one_time_prekeys_by_user_device
            SET used = true
            WHERE user_id = %s AND device_id = %s AND prekey_id = %s
            ''',
            (user_id, device_id, one_time_row['prekey_id'])
        )

        return {
            'identity_key': row['identity_key'],
            'registration_id': row.get('registration_id', 0),
            'signed_prekey': {
                'keyId': row['signed_prekey_id'],
                'publicKey': row['signed_prekey'],
                'signature': row['signature']
            },
            'one_time_prekeys': {
                one_time_row['prekey_id']: one_time_row['prekey']
            }
        }
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail='Internal Server Error'
        )
    
@router.post('/api/prekeys/{user_id}/{device_id}')
async def upload_prekey_bundle(
    bundle: PrekeyBundle,
    user_id: str = user_id_validation,
    device_id: UUID = Path(...),
):
    try:
        print('bundle', bundle)
        session.execute(
            '''
            INSERT INTO prekeys_by_user_device (
                user_id, device_id, identity_key,
                signed_prekey_id, signed_prekey, signature,
                registration_id, signed_at, last_updated
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, toTimestamp(now()), toTimestamp(now()))
            ''',
            (
                user_id,
                device_id,
                bundle.identity_key,
                bundle.signed_prekey.key_id,
                bundle.signed_prekey.public_key,
                bundle.signed_prekey.signature,
                bundle.registration_id
            )
        )
        return {'status': 'ok'}
    except Exception as e:
        print('Error uploading prekey bundle:', e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail='Internal Server Error'
        )
