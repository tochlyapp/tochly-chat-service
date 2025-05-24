from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any

@dataclass
class RoomDetailsParams:
    team_id: str
    room_id: str
    user_id: str
    participant_id: str
    last_message: str
    last_message_type: str
    created_at: datetime
    cookies: Dict[str, str]

    @classmethod
    def from_row(cls, row: Any, team_id: str, user_id: str, cookies: Dict[str, str]) -> 'RoomDetailsParams':
        return cls(
            team_id=team_id,
            room_id=row.room_id,
            user_id=user_id,
            participant_id=row.participant_id,
            last_message=row.last_message,
            last_message_type=row.last_message_type,
            created_at=row.created_at,
            cookies=cookies,
        )
