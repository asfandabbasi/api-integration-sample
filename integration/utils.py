import uuid
import requests

from datetime import datetime

from big_chat.main import conversations, advisors

BIG_CHAT_API = "http://localhost:8267"
OUR_API = "http://localhost:8266"


def int_to_uuid(int_value: int) -> uuid.UUID:
    # Ensure the integer value can fit into a 128-bit UUID
    if int_value < 0 or int_value >= 2 ** 128:
        raise ValueError("Integer value out of range for UUID")

    # Convert integer to a 16-byte (128-bit) big-endian representation
    int_bytes = int_value.to_bytes(16, byteorder='big')

    # Create UUID from the 16-byte representation
    return str(uuid.UUID(bytes=int_bytes))


def save_chat(event, logger, agent_id=None):
    try:
        data = {"external_id": int_to_uuid(event["conversation_id"]), "agent_id": None,
                "started_at": datetime.fromtimestamp(event["event_at"]).isoformat()}

        chat = requests.post(f"{OUR_API}/chats", json=data)
        if chat.status_code==201:
            logger.info(f"Created chat {chat.json()['chat_id']}.")
        else:
            logger.error(f"Failed to create chat")
    except Exception as e:
        print(e)

def patch_chat(event, logger):
    try:
        data = {"external_id": int_to_uuid(event["conversation_id"])}
        data = {**data, "ended_at": event.get("event_at")} if event.get("event_name") == "END" else data
        if event.get("data") and event.get("data", {}).get("new_advisor_id"):
            advisor = requests.get(f"{BIG_CHAT_API}/advisors/{event.get('data', {}).get('new_advisor_id')}")
            parameters = {"email": advisor.json()["email_address"]}
            agent = requests.get(f"{OUR_API}/agents", params=parameters)
            if len(agent.json()) == 0:
                save_agent(event, logger)
                agent = requests.get(f"{OUR_API}/agents", params=parameters)
            data["agent_id"] = agent.json()[0]["agent_id"]

        data = {**data, "started_at": event.get("started_at")} if event.get("started_at") else data
        parameters = {"external_id": int_to_uuid(event["conversation_id"])}

        chat = requests.get(f"{OUR_API}/chats", params=parameters)
        if len(chat.json()) > 0:
            chat_patch = requests.patch(f"{OUR_API}/chats/{chat.json()[0]['chat_id']}", json=data)
        else:
            save_chat(event, logger)
            return

        if chat_patch.status_code != 204:
            logger.error("Failed to patch chat")
        else:
            logger.info(f"Patched chat {chat.json()[0]['chat_id']}")
    except Exception as e:
        print(e)

def save_agent(event, logger):
    try:
        advisor_id = event["data"].get("new_advisor_id")
        advisor = requests.get(f"{BIG_CHAT_API}/advisors/{advisor_id}")
        data = {"agent_id": int_to_uuid(advisor.json()["advisor_id"]), "name": advisor.json()["name"],
                "email": advisor.json()["email_address"]}
        agent = requests.post(f"{OUR_API}/agents", json=data)
        if agent.status_code == 201:
            logger.info(f"Created Agent {agent.json()['agent_id']}.")
        else:
            logger.error("Failed to create Agent")

        patch_chat(event, logger)
    except Exception as e:
        print(e)


def save_message(event, logger):
    try:
        data = {"chat_id": int_to_uuid(event["conversation_id"]), "sent_at": event["event_at"],
            "text": event["data"]["message"]}

        parameters = {"external_id": int_to_uuid(event["conversation_id"])}
        chat = requests.get(f"{OUR_API}/chats", params=parameters)

        if chat.status_code != 200 or len(chat.json()) == 0:
            # conversation = requests.get(f"{BIG_CHAT_API}/conversations/{event['conversation_id']}")

            save_chat(event, logger)
            chat = requests.get(f"{OUR_API}/chats", params=parameters)

            response = requests.post(f"{OUR_API}/chats/{int_to_uuid(event['conversation_id'])}/messages", json=data)
        else:

            response = requests.post(f"{OUR_API}/chats/{chat.json()[0]['chat_id']}/messages", json=data)

        if response.status_code == 200:
            logger.info(f"Created message.")
        else:
            logger.error("Failed to save message")
    except Exception as e:
        print(e)