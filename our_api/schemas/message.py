from datetime import datetime
from typing import Optional

from pydantic import Field, BaseModel, constr
from uuid import UUID


class MessageBase(BaseModel):
    chat_id: Optional[UUID] = Field(description="Chat the message belongs to", default=None)
    agent_id: Optional[UUID] = Field(
        description="Agent that sent the message (empty if it's a customer message).", default=None
    )
    sent_at: datetime = Field(description="When the message was sent.")
    text: constr(strip_whitespace=True, min_length=2) = Field(description="Message content.")


class MessageCreate(MessageBase):
    pass


class Message(MessageBase):
    message_id: UUID

    class Config:
        from_attributes = True
