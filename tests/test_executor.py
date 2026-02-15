import unittest
from unittest.mock import patch

from core.executor import RPAExecutor
from core.schema import Status


class TestRPAExecutor(unittest.TestCase):
    def test_run_not_found(self):
        result = RPAExecutor.run("missing_rpa", {})
        self.assertEqual(result["status"], Status.NOT_FOUND)

    def test_run_success(self):
        mock_registry = {
            "demo": {
                "func": lambda text: f"ok:{text}",
                "desc": "demo",
                "params": ["text"],
            }
        }
        mock_config = {
            "system": {"max_retry": 0, "timeout": 5},
            "rpa": {"log_file": "logs/rpa.log"},
        }

        with patch("core.executor.RPA_REGISTRY", mock_registry), patch("core.executor.load_config", return_value=mock_config):
            result = RPAExecutor.run("demo", {"text": "hello"})

        self.assertEqual(result["status"], Status.SUCCESS)
        self.assertEqual(result["data"], "ok:hello")


if __name__ == "__main__":
    unittest.main()
