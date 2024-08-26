from sqlalchemy import Column, UUID, TIMESTAMP, Text, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base


class Chat(Base):
    __tablename__ = "chats"
    chat_id = Column(UUID, primary_key=True)
    agent_id = Column(UUID, ForeignKey("agents.agent_id"))
    started_at = Column(TIMESTAMP, nullable=False)
    ended_at = Column(TIMESTAMP)
    external_id = Column(Text, nullable=False, unique=True)
    messages = relationship("Message")
