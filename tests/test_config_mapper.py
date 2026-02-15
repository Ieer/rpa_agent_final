import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCAL_NANOBOT_ROOT = ROOT / "nanobot"
if str(LOCAL_NANOBOT_ROOT) not in sys.path:
    sys.path.insert(0, str(LOCAL_NANOBOT_ROOT))

from nanobot_bridge.config_mapper import map_config_to_nanobot_runtime


class TestConfigMapper(unittest.TestCase):
    def test_explicit_provider_and_headers(self):
        cfg = {
            "system": {"restrict_to_workspace": True},
            "llm": {
                "provider": "custom",
                "base_url": "http://127.0.0.1:11434/v1",
                "api_key": "ollama",
                "model": "qwen2:1.5b",
                "headers": {"X-Test": "1"},
                "max_tool_iterations": 12,
                "memory_window": 34,
            },
        }

        runtime = map_config_to_nanobot_runtime(cfg)
        self.assertEqual(runtime.provider.provider_name, "custom")
        self.assertEqual(runtime.provider.default_model, "qwen2:1.5b")
        self.assertEqual(runtime.provider.extra_headers["X-Test"], "1")
        self.assertEqual(runtime.agent.max_iterations, 12)
        self.assertEqual(runtime.agent.memory_window, 34)
        self.assertTrue(runtime.agent.restrict_to_workspace)

    def test_model_routes_mapping(self):
        cfg = {
            "llm": {
                "model": "mini",
                "model_routes": {"mini": "qwen2.5:3b"},
            }
        }

        runtime = map_config_to_nanobot_runtime(cfg)
        self.assertEqual(runtime.provider.default_model, "qwen2.5:3b")


if __name__ == "__main__":
    unittest.main()
