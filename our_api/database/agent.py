from sqlalchemy import Column, UUID, Text

from .base import Base


class Agent(Base):
    __tablename__ = "agents"
    agent_id = Column(UUID, primary_key=True)
    name = Column(Text, nullable=False, unique=True)
    email = Column(Text, nullable=False, unique=True)
