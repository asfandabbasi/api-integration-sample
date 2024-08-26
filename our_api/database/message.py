from sqlalchemy import Column, UUID, TIMESTAMP, Text, ForeignKey

from .base import Base


class Message(Base):
    __tablename__ = "messages"
    message_id = Column(UUID, primary_key=True)
    chat_id = Column(UUID, ForeignKey("chats.chat_id"))
    agent_id = Column(UUID, ForeignKey("agents.agent_id"))
    sent_at = Column(TIMESTAMP, nullable=False)
    text = Column(Text, nullable=False)
