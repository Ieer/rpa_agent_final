import unittest
from unittest.mock import Mock, patch

import nanobot_tool


class TestNanoBotTool(unittest.TestCase):
    def test_execute_rpa_skill_mode(self):
        cfg = {"system": {"mode": "skill"}, "api": {"host": "127.0.0.1", "port": 8976, "api_key": "k"}}
        with patch("nanobot_tool.load_config", return_value=cfg), patch("nanobot_tool.SkillAdapter.run", return_value={"status": "success"}) as run_mock:
            result = nanobot_tool.execute_rpa("demo", {"x": 1})
        run_mock.assert_called_once_with("demo", {"x": 1})
        self.assertEqual(result["status"], "success")

    def test_execute_rpa_api_mode(self):
        cfg = {"system": {"mode": "api"}, "api": {"host": "127.0.0.1", "port": 8976, "api_key": "k"}}
        mock_resp = Mock()
        mock_resp.json.return_value = {"status": "success"}
        mock_resp.raise_for_status.return_value = None

        with patch("nanobot_tool.load_config", return_value=cfg), patch("nanobot_tool.requests.post", return_value=mock_resp) as post_mock:
            result = nanobot_tool.execute_rpa("demo", {"x": 1})

        self.assertEqual(result["status"], "success")
        self.assertTrue(post_mock.called)

    def test_register_tool(self):
        class DummyRegistry:
            def __init__(self):
                self.added = []

            def has(self, name):
                return False

            def register(self, tool):
                self.added.append(tool)

        registry = DummyRegistry()
        nanobot_tool.register_rpa_tool(registry)
        self.assertEqual(len(registry.added), 1)
        self.assertEqual(registry.added[0].name, "execute_rpa")


if __name__ == "__main__":
    unittest.main()
