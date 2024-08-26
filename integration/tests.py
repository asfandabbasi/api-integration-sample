import unittest
from unittest.mock import patch, MagicMock
import uuid
from datetime import datetime

# Import the methods you want to test
from utils import int_to_uuid, save_chat, patch_chat, save_agent, save_message


class TestChatMethods(unittest.TestCase):

    def test_int_to_uuid(self):
        int_value = 123456789012345678901234567890123456
        result = int_to_uuid(int_value)
        self.assertEqual(result, str(uuid.UUID(int=int_value)))

        # Test for out of range
        with self.assertRaises(ValueError):
            int_to_uuid(2**128)

    @patch('utils.requests.post')
    @patch('utils.requests.get')
    def test_save_chat(self, mock_get, mock_post):
        # Mock response for GET request
        mock_post.return_value.json.return_value = {"chat_id": "test_chat_id"}
        mock_post.return_value.status_code = 201
        mock_logger = MagicMock()

        event = {"conversation_id": 123456, "event_at": datetime.now().timestamp()}

        save_chat(event, mock_logger)

        mock_post.assert_called_once_with(
            "http://localhost:8266/chats",
            json={
                "external_id": int_to_uuid(event["conversation_id"]),
                "agent_id": None,
                "started_at": datetime.fromtimestamp(event["event_at"]).isoformat()
            }
        )
        mock_logger.info.assert_called_with("Created chat test_chat_id.")

    @patch('utils.requests.patch')
    @patch('utils.requests.get')
    def test_patch_transfer_chat(self, mock_get, mock_patch):
        mock_logger = MagicMock()

        # Mock response for GET request to fetch advisor and chat
        mock_get.side_effect = [
            MagicMock(json=lambda: {"email_address": "test@example.com"}),  # advisor get
            MagicMock(json=lambda: [{"agent_id": "test_agent_id"}]),  # agent get
            MagicMock(json=lambda: [{"chat_id": "test_chat_id"}]),  # chat get
        ]
        mock_patch.return_value.status_code = 204

        event = {
            "conversation_id": 123456,
            "event_at": datetime.now().timestamp(),
            "event_name": "TRANSFER",
            "data": {"new_advisor_id": 1}
        }

        patch_chat(event, mock_logger)

        mock_logger.info.assert_called_with("Patched chat test_chat_id")

    @patch('utils.requests.patch')
    @patch('utils.requests.get')
    def test_patch_end_chat(self, mock_get, mock_patch):
        mock_logger = MagicMock()

        # Mock response for GET request to fetch advisor and chat
        mock_get.side_effect = [
            MagicMock(json=lambda: [{"chat_id": "test_chat_id"}]),  # chat get
            MagicMock(json=lambda: {"email_address": "test@example.com"}),  # advisor get
            MagicMock(json=lambda: [{"agent_id": "test_agent_id"}]),  # agent get
        ]
        mock_patch.return_value.status_code = 204

        event = {
            "conversation_id": 123456,
            "event_at": datetime.now().timestamp(),
            "event_name": "END",
            "data": None
        }

        patch_chat(event, mock_logger)

        mock_logger.info.assert_called_with("Patched chat test_chat_id")

    @patch('utils.requests.post')
    @patch('utils.requests.get')
    def test_save_agent(self, mock_get, mock_post):
        mock_logger = MagicMock()

        # Mock response for GET request to fetch advisor
        mock_get.side_effect = [
            MagicMock(json=lambda: {"advisor_id": 1, "name": "Test Advisor", "email_address": "test@example.com"}),  # advisor get
            MagicMock(json=lambda: [{"agent_id": "test_agent_id"}]),  # agent get after save
        ]

        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {"agent_id": "test_agent_id"}

        event = {"data": {"conversation_id":1,"new_advisor_id": 1, "event_at": datetime.now().timestamp()}}

        save_agent(event, mock_logger)

        mock_logger.info.assert_called_with("Created Agent test_agent_id.")

    @patch('utils.requests.post')
    @patch('utils.requests.get')
    def test_save_message(self, mock_get, mock_post):
        mock_logger = MagicMock()

        # Mock response for GET request to fetch chat
        mock_get.side_effect = [
            MagicMock(status_code=200, json=lambda: [{"chat_id": "test_chat_id"}]),  # chat get
        ]

        mock_post.return_value.status_code = 200

        event = {
            "conversation_id": 123456,
            "event_at": datetime.now().timestamp(),
            "data": {"message": "Test message"}
        }

        save_message(event, mock_logger)

        mock_logger.info.assert_called_with("Created message.")

if __name__ == '__main__':
    unittest.main()


