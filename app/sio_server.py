from socketio import AsyncServer
from socketio import AsyncRedisManager

from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger('socketio')

origins = settings.CORS_ORIGINS.split(',')
redis_url = settings.REDIS_URL

manager = AsyncRedisManager(redis_url)
sio = AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=origins,
    client_manager=manager,
    cookie={
        'name': 'io',
        'path': '/',
        'httponly': 'True',
        'secure': 'False',
        'samesite': 'lax'
    },
    logger=logger,
    engineio_logger=logger,
)
