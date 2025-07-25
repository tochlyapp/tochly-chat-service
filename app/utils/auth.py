from fastapi import HTTPException, status
import aiohttp

from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger('socketio')

def _normalize_cookies(cookies):
    if isinstance(cookies, dict):
        return cookies
    return {k: v.value for k, v in cookies.items()}

async def verify_cookies(cookies):
    cookies_dict = _normalize_cookies(cookies)

    async with aiohttp.ClientSession(cookies=cookies_dict) as http_client:
        async with http_client.post(
            f'{settings.BACKEND_BASE_URL}/jwt/verify/',
            cookies=cookies_dict,
        ) as response:
            if response.status != 200:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
