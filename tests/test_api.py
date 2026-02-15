import unittest
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from adapter.api import app


class TestAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_list_auth_fail(self):
        response = self.client.get("/api/rpa/list", headers={"api_key": "bad"})
        self.assertEqual(response.status_code, 403)

    def test_list_success(self):
        cfg = {
            "api": {"api_key": "k"},
        }
        with patch("adapter.api.load_config", return_value=cfg):
            response = self.client.get("/api/rpa/list", headers={"api_key": "k"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("data", body)

    def test_chat_send(self):
        cfg = {
            "api": {"api_key": "k"},
            "chat": {"default_session": "dash:default"},
        }

        class DummyService:
            def submit(self, message, session_key):
                self.message = message
                self.session_key = session_key
                return "run123"

        svc = DummyService()
        with patch("adapter.api.load_config", return_value=cfg), patch("adapter.api.get_chat_service", return_value=svc):
            response = self.client.post("/api/chat/send", json={"message": "hello"}, headers={"api_key": "k"})

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["run_id"], "run123")
        self.assertEqual(body["session_key"], "dash:default")

    def test_chat_status(self):
        cfg = {
            "api": {"api_key": "k"},
        }

        class DummyService:
            def get_status(self, run_id):
                return {"run_id": run_id, "status": "running"}

        with patch("adapter.api.load_config", return_value=cfg), patch("adapter.api.get_chat_service", return_value=DummyService()):
            response = self.client.get("/api/chat/status/run123", headers={"api_key": "k"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["status"], "running")

    def test_chat_history(self):
        cfg = {
            "api": {"api_key": "k"},
            "chat": {"default_session": "dash:default"},
        }

        class DummyService:
            def get_history(self, session_key, limit):
                return [{"role": "user", "content": "hello"}]

        with patch("adapter.api.load_config", return_value=cfg), patch("adapter.api.get_chat_service", return_value=DummyService()):
            response = self.client.get("/api/chat/history", headers={"api_key": "k"})

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["session_key"], "dash:default")
        self.assertEqual(body["data"][0]["content"], "hello")

    def test_embedding_test_success(self):
        cfg = {
            "api": {"api_key": "k"},
            "embedding": {
                "enabled": True,
                "base_url": "http://127.0.0.1:1234/v1",
                "model": "text-embedding-qwen3-embedding-0.6b",
                "api_key": "lm-studio",
                "headers": {},
            },
        }

        mock_resp = Mock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {
            "data": [{"embedding": [0.1, 0.2, 0.3]}],
            "usage": {"prompt_tokens": 3, "total_tokens": 3},
        }

        with patch("adapter.api.load_config", return_value=cfg), patch("adapter.api.requests.post", return_value=mock_resp):
            response = self.client.post("/api/embedding/test", json={"input_text": "hello"}, headers={"api_key": "k"})

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["dimension"], 3)

    def test_embedding_test_disabled(self):
        cfg = {
            "api": {"api_key": "k"},
            "embedding": {
                "enabled": False,
            },
        }

        with patch("adapter.api.load_config", return_value=cfg):
            response = self.client.post("/api/embedding/test", json={"input_text": "hello"}, headers={"api_key": "k"})

        self.assertEqual(response.status_code, 400)
        self.assertIn("embedding 未啟用", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
