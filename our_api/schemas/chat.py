from datetime import datetime
from typing import Optional

from pydantic import Field, BaseModel
from uuid import UUID


class ChatBase(BaseModel):
    agent_id: Optional[UUID] = Field(description="Agent that handled the chat.", default=None)
    started_at: datetime = Field(description="When the chat started.")
    ended_at: Optional[datetime] = Field(
        description="When the chat ended (will be undefined if the chat is ongoing.",
        default=None,
    )
    external_id: str = Field(description="ID from other systems used for reference.")


class ChatCreate(ChatBase):
    pass


class ChatUpdate(BaseModel):
    agent_id: Optional[UUID] = Field(description="Agent that handled the chat.", default=None)
    started_at: Optional[datetime] = Field(description="When the chat started.", default=None)
    ended_at: Optional[datetime] = Field(
        description="When the chat ended (will be undefined if the chat is ongoing.",
        default=None,
    )


class Chat(ChatBase):
    chat_id: UUID

    class Config:
        from_attributes = True
