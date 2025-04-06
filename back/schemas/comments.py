from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class CommentBase(BaseModel):
    content: str

class CommentCreate(CommentBase):
    pass

class CommentInDB(CommentBase):
    id: int
    timestamp: datetime
    approved: bool
    user_id: int
    profile_id: int
    user_name: str
    notification_id: Optional[int]

