from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional


class StartChatValidator(BaseModel):
    team_id: str = Field(
        ..., min_length=9, 
        max_length=10, 
        pattern=r'^[a-zA-Z0-9]+$',
    )
    receiver_id: str = Field(
        ..., min_length=1,
        max_length=10, 
        pattern=r'^[0-9]+$',
    )

    @field_validator('*', mode='before')
    def strip_strings(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator('team_id', 'receiver_id')
    def validate_ids_not_empty(cls, v):
        if not v:
            raise ValueError("ID cannot be empty")
        return v

    
class SendChatMessageValidator(BaseModel):
    room_id: str = Field(
        ..., 
        min_length=1, 
        max_length=10, 
        pattern=r'^[a-zA-Z0-9_]+$',
    )
    receiver_id: str = Field(
        ..., 
        min_length=1, 
        max_length=10, 
        pattern=r'^[0-9]+$',
    )
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

    @field_validator('*', mode='before')
    @classmethod
    def strip_strings(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v

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
            for field_name in ['attachment_url', 'file_name', 'file_size', 'mime_type']:
                if not getattr(self, field_name):
                    raise ValueError(f'{field_name} is required for non-text messages')
        return self
