from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    BASE_URL: str
    BACKEND_BASE_URL: str
    REDIS_URL: str
    CORS_ORIGINS: str = 'http://localhost:3000'
    DEBUG: bool = False
    SECRET_KEY: str
    TOKEN_HASH_ALGORITHM: str = 'HS256"'
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = 'ignore'  # Ignore extra env vars

def get_settings():
    return Settings(_env_file=".env")

settings = get_settings()
