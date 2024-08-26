from pydantic import Field, constr, BaseModel
from uuid import UUID


class AgentBase(BaseModel):
    name: constr(min_length=2, strip_whitespace=True) = Field(description="Agent's name.")
    email: constr(min_length=2, strip_whitespace=True) = Field(description="Agent's email address.")


class AgentCreate(AgentBase):
    pass


class Agent(AgentBase):
    agent_id: UUID

    class Config:
        from_attributes = True
