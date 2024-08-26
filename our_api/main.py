import logging
import sys
from http import HTTPStatus
from typing import Optional, Annotated, List

from sqlalchemy import select, exists
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import schemas

from uuid import uuid4, UUID

from database import Base, SessionLocal, engine
import database


import uvicorn
from fastapi import FastAPI, HTTPException, Response, Depends, Query


def get_session() -> Session:
    """
    Get a database session.
    """
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


app = FastAPI(title="Fake API", version="1.0.0")

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler(sys.stdout)
log_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
stream_handler.setFormatter(log_formatter)
logger.addHandler(stream_handler)
logger.info("API is starting up")


@app.post(
    "/chats",
    response_model=schemas.Chat,
    status_code=HTTPStatus.CREATED,
    summary="Create a chat",
    tags=["Chats"],
)
def post_chat(
    data: schemas.ChatCreate,
    response: Response,
    session: Session = Depends(get_session),
):
    """
    Create a chat.
    """

    logging.info("Creating a chat")

    # Ensure the agent exists.
    if data.agent_id and not session.scalar(select(exists().where(database.Agent.agent_id == data.agent_id))):
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="That agent does not exist.")

    chat_id = uuid4()
    chat = database.Chat(
        agent_id=data.agent_id,
        chat_id=chat_id,
        started_at=data.started_at,
        ended_at=data.ended_at,
        external_id=data.external_id,
    )

    session.add(chat)

    try:
        session.commit()
    except IntegrityError:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="A chat with that external ID already exists.",
        )

    session.refresh(chat)
    response.headers["Location"] = f"/chats/{chat_id}"
    return chat


@app.patch(
    "/chats/{chat_id}",
    status_code=HTTPStatus.NO_CONTENT,
    summary="Edit a chat",
    tags=["Chats"],
)
def patch_chat(chat_id: UUID, data: schemas.ChatUpdate, session: Session = Depends(get_session)):
    """
    Edit a chat.
    """
    chat = session.get(database.Chat, chat_id)
    if not chat:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Chat not found")

    # Ensure the agent exists.
    if data.agent_id and not session.scalar(select(exists().where(database.Agent.agent_id == data.agent_id))):
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="That agent does not exist.")

    for field in data.dict(exclude_unset=True):
        setattr(chat, field, getattr(data, field))

    session.commit()

    return {}


@app.post("/chats/{chat_id}/messages", summary="Create a message", tags=["Messages"])
def post_chat_message(chat_id: UUID, data: schemas.MessageCreate, session: Session = Depends(get_session)):
    """
    Create a chat message.
    """
    chat = session.get(database.Chat, chat_id)
    if not chat:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Chat not found")

    # Ensure the agent exists.
    if data.agent_id and not session.scalar(select(exists().where(database.Agent.agent_id == data.agent_id))):
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="That agent does not exist.")

    message_id = uuid4()
    message = database.Message(
        message_id=message_id,
        agent_id=data.agent_id,
        chat_id=chat_id,
        sent_at=data.sent_at,
        text=data.text,
    )

    session.add(message)
    session.commit()
    session.refresh(message)

    return chat


@app.get(
    "/chats/{chat_id}/messages",
    response_model=List[schemas.Message],
    summary="Get a chat's messages",
    tags=["Messages"],
)
def get_chat_messages(chat_id: UUID, session: Session = Depends(get_session)):
    """
    Get a chat's messages.
    """
    chat = session.get(database.Chat, chat_id)
    if not chat:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Chat not found")

    return chat.messages


@app.get(
    "/chats/{chat_id}",
    response_model=schemas.Chat,
    summary="Get a chat",
    tags=["Chats"],
)
def get_chat(chat_id: UUID, session: Session = Depends(get_session)):
    """
    Get a chat.
    """
    chat = session.get(database.Chat, chat_id)
    if not chat:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Chat not found")

    return chat


@app.get(
    "/chats",
    response_model=List[schemas.Chat],
    summary="Get several chats",
    tags=["Chats"],
)
def get_chats(
    external_id: Annotated[
        Optional[str],
        Query(description="Optionally filter to find chats with a given external ID."),
    ] = None,
    session: Session = Depends(get_session),
):
    """
    Get chats.
    """
    query = select(database.Chat)
    if external_id:
        query = query.where(database.Chat.external_id == external_id)

    chats = session.scalars(query)
    return chats.all()


@app.post(
    "/agents",
    response_model=schemas.Agent,
    status_code=HTTPStatus.CREATED,
    summary="Create an agent",
    tags=["Agents"],
)
def post_agent(
    data: schemas.AgentCreate,
    response: Response,
    session: Session = Depends(get_session),
):
    """
    Create an agent.
    """
    agent_id = uuid4()
    agent = database.Agent(agent_id=agent_id, name=data.name, email=data.email)
    session.add(agent)
    session.commit()
    session.refresh(agent)

    response.headers["Location"] = f"/agents/{agent_id}"
    return agent


@app.get("/agents/{agent_id}", summary="Get an agent", tags=["Agents"])
def get_agent(agent_id: UUID, session: Session = Depends(get_session)):
    """
    Get an agent.
    """
    agent = session.get(database.Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Agent not found")

    return agent


@app.get("/agents", response_model=List[schemas.Agent], summary="Get agents", tags=["Agents"])
def get_agents(
    name: Annotated[
        Optional[str],
        Query(description="Optionally filter to find agents with a given name"),
    ] = None,
    email: Annotated[
        Optional[str],
        Query(description="Optionally filter to find agents with a given email address"),
    ] = None,
    session: Session = Depends(get_session),
):
    """
    Get agents.
    """
    query = select(database.Agent)
    if email:
        query = query.where(database.Agent.email == email)

    if name:
        query = query.where(database.Agent.name == name)

    chats = session.scalars(query)
    return chats.all()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8266)
