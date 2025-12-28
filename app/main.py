from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from socketio import ASGIApp

from .sio_server import sio, origins
from .services import socketio
from .api.routes import chat, prekeys

fastapi_app = FastAPI(
    docs_url='/api/docs',
    openapi_url='/api/openapi.json',
    redoc_url=None
)

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

fastapi_app.include_router(chat.router)
fastapi_app.include_router(prekeys.router)

app = ASGIApp(
    socketio_server=sio,
    other_asgi_app=fastapi_app,
    socketio_path='socket.io',
)
