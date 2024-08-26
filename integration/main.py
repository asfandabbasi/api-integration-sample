from datetime import datetime, timedelta
from http.client import responses
from time import sleep
from unittest.mock import patch

import requests
import logging

from integration.utils import save_chat, patch_chat, save_message, save_agent
from utils import int_to_uuid

FORMAT = "%(asctime)s | %(levelname)-5s | %(message)s"

logging.basicConfig(format=FORMAT, datefmt="%I:%M:%S %p")
logger = logging.getLogger()
logger.setLevel(logging.INFO)

BIG_CHAT_API = "http://localhost:8267"
OUR_API = "http://localhost:8266"

if __name__ == "__main__":
    # Get events from BigChat.
    while True:
        try:
            parameters = {"start_at": (datetime.now() - timedelta(seconds=10))}
            events = requests.get(f"{BIG_CHAT_API}/events", params=parameters)
            if events.status_code == 200:
                for event in events.json()["events"]:
                    parameters = {"conversation_id": event["conversation_id"]}
                    # chat = requests.get(f"{OUR_API}/chats/{int_to_uuid(event['conversation_id'])}")
                    if event["event_name"] == "START":
                        save_chat(event, logger)

                    elif event["event_name"] == "TRANSFER":
                        save_agent(event, logger)

                    elif event["event_name"] == "MESSAGE":
                        save_message(event, logger)

                    elif event["event_name"] == "END":
                        patch_chat(event, logger)
                sleep(0)
        except Exception as e:
            print(e)