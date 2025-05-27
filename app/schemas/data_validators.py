from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional

team_id_validation = Field(
    ..., min_length=9, 
    max_length=10, 
    pattern=r'^[a-zA-Z0-9]+$',
)
user_id_validation = Field(
    ..., min_length=1,
    max_length=10, 
    pattern=r'^[0-9]+$',
)
room_id_validation = Field(
    ..., 
    min_length=1, 
    max_length=10, 
    pattern=r'^[a-zA-Z0-9_]+$',
)

class BaseValidator(BaseModel):
    @field_validator('*', mode='before')
    def strip_strings(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v


class StartChatValidator(BaseValidator):
    team_id: str = team_id_validation
    receiver_id: str = user_id_validation


class SendChatMessageValidator(BaseValidator):
    room_id: str = room_id_validation
    receiver_id: str = user_id_validation
    message_type: str = Field(
        ..., 
        min_length=1, 
        max_length=10, 
        pattern=r'^(text|image|video|file|audio)$',
    )
    content: Optional[str] = Field(
        None, 
        max_length=1000,
    )
    attachment_url: Optional[str] = Field(
        None, 
        max_length=200,
    )
    file_name: Optional[str] = Field(
        None,
        max_length=100,
        pattern=r'^[a-zA-Z0-9_\-\. ]+$',
    )
    file_size: Optional[int] = Field(
        None,
        ge=1,
        le=10_000_000,
        example=1024,
        description='File size in bytes'
    )
    mime_type: Optional[str] = Field(
        None,
        max_length=50,
        pattern=r'^[a-z]+\/[a-z0-9\-\.\+]+$',
        example='image/png',
        description='MIME type of attachment'
    )

    @field_validator('content')
    def validate_content(cls, v, info):
        if info.values.get('message_type') == 'text' and not v:
            raise ValueError('Content is required for text messages')
        return v
    
    @model_validator(mode='after')
    def validate_fields(self):
        if self.message_type == 'text':
            if not self.content:
                raise ValueError('Content is required for text messages')
        else:
            missing_fields = [
                f for f in ['attachment_url', 'file_name', 'file_size', 'mime_type']
                if not getattr(self, f)
            ]
            if missing_fields:
                raise ValueError(
                    f"Missing fields for non-text messages: {', '.join(missing_fields)}"
                )
            
        return self


class QueryParams(BaseValidator):
    team_id: str = team_id_validation
    user_id: str = user_id_validation
    search: Optional[str] = Field(None, max_length=50)
    limit: int = Field(10, ge=1, le=100)
    skip: int = Field(0, ge=0)


class RoomMessagesQueryParams(QueryParams):
    room_id: str = room_id_validation
    before: Optional[datetime] = Field(None)
