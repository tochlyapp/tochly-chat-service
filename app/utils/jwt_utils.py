import jwt
from app.config.settings import settings

def decode_jwt(token: str):
    try:
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.TOKEN_HASH_ALGORITHM])
        return decoded
    except jwt.InvalidTokenError as e:
        print(f'JWT decoding error: {e}')
        return None
