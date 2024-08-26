import sys
from datetime import datetime, timezone
from functools import partial
from http import HTTPStatus
from random import random, randrange, choice
from typing import List, Optional
import logging
import uvicorn
from faker import Faker
from requests import PreparedRequest
from faker.providers import date_time, misc, lorem, internet
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

app = FastAPI(title="Big Chat", version="23.4.1")
faker = Faker("en_GB")
faker.add_provider(lorem)
faker.add_provider(misc)
faker.add_provider(internet)
faker.add_provider(date_time)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler(sys.stdout)
log_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
stream_handler.setFormatter(log_formatter)
logger.addHandler(stream_handler)

logger.info("API is starting up")


class Advisor(BaseModel):
    advisor_id: int = Field(description="Advisor identifier")
    name: str = Field(description="Advisor's full name")
    email_address: str = Field(description="Advisor's email address")


class Event(BaseModel):
    conversation_id: int = Field(description="In which conversation the event took place")
    event_name: str = Field(description="Name of the event")
    event_at: int = Field(description="When the event occurred")
    data: Optional[dict] = Field(description="Extra data associated with the event", default=None)


class Conversation(BaseModel):
    events: List[Event] = Field(description="Conversation events")
    conversation_id: int = Field(description="Identifier for the conversation")
    advisor_id: int = Field(description="Which advisor handled or is handling a conversation")


def _create_advisor(advisor_id: int = None) -> Advisor:
    name = faker.name()
    return Advisor(
        advisor_id=advisor_id or len(advisors) + 1,
        name=faker.name(),
        email_address=f"{name.replace(' ', '_').lower()}@company.com",
    )


# Make some initial advisors.
advisors = {advisor.advisor_id: advisor for advisor in [_create_advisor(advisor_id + 1) for advisor_id in range(10)]}


conversations = {
    1: Conversation(
        events=[
            Event(
                conversation_id=1,
                event_name="START",
                event_at=int(datetime.now().timestamp()),
            )
        ],
        conversation_id=1,
        advisor_id=1,
    )
}


def _has_event(event_name: str, conversation: Conversation) -> bool:
    """
    Check if a conversation has an event.
    """
    return any(event for event in conversation.events if event.event_name.upper() == event_name.upper())


def _choose_random_advisor_id(exclude_advisor_id: int = None) -> int:
    possible_advisors = (
        advisors
        if not isinstance(exclude_advisor_id, int)
        else [advisor for advisor in advisors.values() if advisor != exclude_advisor_id]
    )
    return choice(possible_advisors).advisor_id


_has_transfer = partial(_has_event, "TRANSFER")
_has_ended = partial(_has_event, "END")


@app.get("/events", summary="Get events.", tags=["Events"])
def get_events(request: Request, start_at: datetime = None, end_at: datetime = None, page: int = 0):
    """
    Get events.
    """

    end_at = end_at if isinstance(end_at, int) else datetime.now(tz=timezone.utc)

    if faker.boolean(0):
        raise HTTPException(HTTPStatus.BAD_GATEWAY, detail="Big Chat is experiencing an issue.")

    # Active conversations can still get events.
    active_conversations = [conversation for conversation in conversations.values() if not _has_ended(conversation)]

    events = []
    logger.debug(f"Found {len(active_conversations):,} active conversation(s).")

    for conversation in active_conversations:
        conversation_events = []

        # Maybe end the conversation.
        if faker.boolean(20) or len(conversation.events) > 20:
            logger.debug(f"Ending conversation {conversation.conversation_id}.")
            conversation_events.append(
                Event(
                    conversation_id=conversation.conversation_id,
                    event_name="END",
                    event_at=int(faker.date_time_between(start_at, end_at).timestamp()),
                )
            )

        # Maybe record a transfer.
        elif conversation.advisor_id and faker.boolean(20) and not _has_transfer(conversation):
            conversation_events.append(
                Event(
                    conversation_id=conversation.conversation_id,
                    event_name="TRANSFER",
                    event_at=int(faker.date_time_between(start_at, end_at).timestamp()),
                    data={
                        "old_advisor_id": conversation.advisor_id,
                        "new_advisor_id": _choose_random_advisor_id(conversation.advisor_id),
                    },
                )
            )

        # Maybe add a message.
        elif faker.boolean(70):
            conversation_events.append(
                Event(
                    conversation_id=conversation.conversation_id,
                    event_name="MESSAGE",
                    event_at=int(faker.date_time_between(start_at, end_at).timestamp()),
                    data={"message": faker.sentence()},
                )
            )

        events += conversation_events

    for index in range(randrange(2)):
        logger.debug("Found a new conversation")
        conversation_id = len(conversations) + 1
        conversation = Conversation(
            events=[
                Event(
                    conversation_id=conversation_id,
                    event_name="START",
                    event_at=int(datetime.now().timestamp()),
                )
            ],
            conversation_id=conversation_id,
            advisor_id=_choose_random_advisor_id(),
        )
        conversations[conversation_id] = conversation
        events += conversation.events

    url = str(request.url)
    prepared_request = PreparedRequest()
    prepared_request.prepare_url(url, {"page": page + 1})

    return {
        "nextPageUrl": prepared_request.url if faker.boolean(20) and len(events) > 0 and page < 1 else None,
        "events": events,
    }


@app.get(
    "/conversations/{conversation_id}",
    response_model=Conversation,
    summary="Get a conversation",
    tags=["Conversations"],
)
def get_conversation(conversation_id: int) -> Conversation:
    """
    Get a single conversation by ID.
    """
    conversation = conversations.get(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Conversation not found")

    return conversation


@app.get(
    "/advisors/{advisor_id}",
    response_model=Advisor,
    summary="Get an advisor",
    tags=["Advisors"],
)
def get_advisor(advisor_id: int) -> Advisor:
    """
    Get a single advisor by ID.
    """
    advisor = advisors.get(advisor_id)
    if advisor is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Advisor not found")

    return advisor


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8267)
