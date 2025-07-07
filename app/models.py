from sqlmodel import SQLModel, Field
from datetime import datetime, timedelta
from typing import Optional

class UserToken(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str
    access_token: str
    refresh_token: str
    expires_at: datetime

    @classmethod
    def from_token_response(cls, user_id: str, data: dict) -> "UserToken":
        expires_in = int(data.get("expires_in", 7200))
        return cls(
            user_id=user_id,
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token", ""),
            expires_at=datetime.utcnow() + timedelta(seconds=expires_in - 60),
        ) 