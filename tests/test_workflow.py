import unittest
from unittest.mock import patch

from workflow.engine import Workflow


class TestWorkflow(unittest.TestCase):
    def test_run(self):
        tasks = [
            {"name": "a", "params": {"x": 1}},
            {"name": "b", "params": {}},
        ]

        with patch("workflow.engine.execute_rpa", side_effect=[{"status": "success"}, {"status": "failed"}]):
            result = Workflow.run(tasks)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["status"], "success")
        self.assertTrue(result[0]["run_id"])
        self.assertEqual(result[0]["run_id"], result[1]["run_id"])
        self.assertEqual(result[0]["step_id"], "step-1")
        self.assertEqual(result[1]["step_id"], "step-2")
        self.assertIn("duration_ms", result[0])
        self.assertIn("started_at", result[0])
        self.assertIn("ended_at", result[0])


if __name__ == "__main__":
    unittest.main()
