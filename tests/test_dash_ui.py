import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

import dash_bootstrap_components as dbc
from dash import html

from dash_ui import app as dash_app


class TestDashUI(unittest.TestCase):
    def test_router(self):
        node = dash_app.router("/rpa-list")
        self.assertIsNotNone(node)

    def test_main_layout_shell_class(self):
        self.assertEqual(dash_app.main_layout.className, "app-shell")

    def test_make_alert_default_duration(self):
        alert = dash_app.make_alert("ok", color="success")
        self.assertEqual(alert.duration, 1800)
        self.assertEqual(alert.className, "app-alert")

    def test_make_alert_override_duration(self):
        alert = dash_app.make_alert(html.Span("x"), color="info", duration=999)
        self.assertEqual(alert.duration, 999)

    def test_run_single_rpa_without_name(self):
        result = dash_app.run_single_rpa(1, None, "{}")
        self.assertIn("請先選擇", result)

    def test_run_workflow_type_error(self):
        result = dash_app.run_workflow(1, "{}")
        self.assertIn("list JSON", result)

    def test_run_workflow_invalid_task(self):
        result = dash_app.run_workflow(1, '[{"params": {}}]')
        self.assertIn("包含 name", result)

    def test_run_workflow_success(self):
        with patch(
            "dash_ui.app.Workflow.run",
            return_value=[
                {
                    "run_id": "run123",
                    "step_id": "step-1",
                    "step_index": 1,
                    "name": "open_notepad",
                    "status": "success",
                    "duration_ms": 20,
                    "started_at": "2026-01-01T00:00:00+00:00",
                    "error_message": None,
                }
            ],
        ):
            view = dash_app.run_workflow(1, '[{"name":"open_notepad","params":{}}]')
        self.assertIsInstance(view, dbc.Container)

    def test_refresh_logs_no_file(self):
        with patch("dash_ui.app.load_config", return_value={"rpa": {"log_file": "logs/not_exists.log"}}):
            text, hint, idx, counter, prev_disabled, next_disabled = dash_app.refresh_logs(0, "", "", 5, 0, 0, "", 0)
        self.assertIn("尚無日誌", text)
        self.assertIn("全部", hint)
        self.assertEqual(idx, 0)
        self.assertIn("0/0", counter)
        self.assertTrue(prev_disabled)
        self.assertTrue(next_disabled)

    def test_parse_run_id_from_search(self):
        self.assertEqual(dash_app.parse_run_id_from_search("?run_id=abc123"), "abc123")
        self.assertEqual(dash_app.parse_run_id_from_search(""), "")

    def test_parse_step_id_from_search(self):
        self.assertEqual(dash_app.parse_step_id_from_search("?step_id=step-2"), "step-2")
        self.assertEqual(dash_app.parse_step_id_from_search(""), "")

    def test_sync_log_filter_from_url_restores_context_lines(self):
        run_id, step_id, context_lines = dash_app.sync_log_filter_from_url(
            "/logs",
            "?run_id=run-1&step_id=step-2",
            10,
        )
        self.assertEqual(run_id, "run-1")
        self.assertEqual(step_id, "step-2")
        self.assertEqual(context_lines, 10)

    def test_build_filtered_log_text(self):
        lines = ["line a", "workflow run_id=abc step_id=step-1", "line c"]
        all_text = dash_app.build_filtered_log_text(lines, "", "")
        filtered_text = dash_app.build_filtered_log_text(lines, "abc", "")
        step_text = dash_app.build_filtered_log_text(lines, "", "step-1")
        combo_text = dash_app.build_filtered_log_text(lines, "abc", "step-1")
        none_text = dash_app.build_filtered_log_text(lines, "not-found", "step-9")
        self.assertIn("line a", all_text)
        self.assertIn("run_id=abc", filtered_text)
        self.assertIn("step_id=step-1", step_text)
        self.assertIn("run_id=abc", combo_text)
        self.assertIn("查無", none_text)

    def test_match_index_helpers(self):
        self.assertEqual(dash_app.clamp_match_index(-1, 3), 0)
        self.assertEqual(dash_app.clamp_match_index(9, 3), 2)
        self.assertEqual(dash_app.next_match_index(0, 3, 1), 1)
        self.assertEqual(dash_app.next_match_index(0, 3, -1), 2)

    def test_move_active_line_to_top(self):
        lines = ["a", "b", "c", "d"]
        reordered, new_index = dash_app.move_active_line_to_top(lines, 2)
        self.assertEqual(reordered[0], "c")
        self.assertEqual(new_index, 0)

    def test_pin_active_line_with_context(self):
        lines = ["l0", "l1", "l2", "l3", "l4", "l5"]
        focused, new_index = dash_app.pin_active_line_with_context(lines, 3, context_lines=1)
        self.assertEqual(focused, ["l3", "l2", "l4"])
        self.assertEqual(new_index, 0)

    def test_pin_active_line_with_context_default_fallback(self):
        lines = ["a", "b", "c"]
        focused, new_index = dash_app.pin_active_line_with_context(lines, 1)
        self.assertEqual(focused[0], "b")
        self.assertEqual(new_index, 0)

    def test_normalize_log_context_lines(self):
        self.assertEqual(dash_app.normalize_log_context_lines(3), 3)
        self.assertEqual(dash_app.normalize_log_context_lines("10"), 10)
        self.assertEqual(dash_app.normalize_log_context_lines(999), 5)

    def test_persist_log_context_lines(self):
        updated = dash_app.persist_log_context_lines(10, 5)
        unchanged = dash_app.persist_log_context_lines(5, 5)
        self.assertEqual(updated, 10)
        self.assertEqual(unchanged, dash_app.no_update)

    def test_save_llm_config_success(self):
        cfg = {"llm": {}}
        with patch("dash_ui.app.load_config", return_value=cfg), patch("dash_ui.app.save_config") as save_mock:
            alert = dash_app.save_llm_config(
                1,
                "http://127.0.0.1:11434/v1",
                "qwen2:1.5b",
                "custom",
                "ollama",
                '{"X-Test":"1"}',
                '{"mini":"qwen2.5:3b"}',
                0.1,
                20,
                50,
                True,
                "http://127.0.0.1:1234/v1",
                "text-embedding-nomic-embed-text-v1.5",
                "lm-studio",
                '{"X-Emb":"1"}',
            )

        self.assertIn("LLM 配置已保存", alert.children)
        self.assertEqual(cfg["llm"]["provider"], "custom")
        self.assertEqual(cfg["llm"]["headers"]["X-Test"], "1")
        self.assertEqual(cfg["llm"]["model_routes"]["mini"], "qwen2.5:3b")
        self.assertEqual(cfg["llm"]["max_tool_iterations"], 20)
        self.assertEqual(cfg["llm"]["memory_window"], 50)
        self.assertTrue(cfg["embedding"]["enabled"])
        self.assertEqual(cfg["embedding"]["model"], "text-embedding-nomic-embed-text-v1.5")
        self.assertEqual(cfg["embedding"]["headers"]["X-Emb"], "1")
        self.assertTrue(save_mock.called)

    def test_save_llm_config_invalid_headers_json(self):
        cfg = {"llm": {}}
        with patch("dash_ui.app.load_config", return_value=cfg), patch("dash_ui.app.save_config") as save_mock:
            alert = dash_app.save_llm_config(
                1,
                "http://127.0.0.1:11434/v1",
                "qwen2:1.5b",
                "custom",
                "ollama",
                '{bad json}',
                '{}',
                0.1,
                20,
                50,
                True,
                "http://127.0.0.1:1234/v1",
                "text-embedding-nomic-embed-text-v1.5",
                "lm-studio",
                '{}',
            )

        self.assertIn("JSON 格式錯誤", alert.children)
        save_mock.assert_not_called()

    def test_prettify_llm_json_texts_success(self):
        headers, routes, emb = dash_app.prettify_llm_json_texts(
            '{"X-Test":"1"}',
            '{"mini":"qwen2.5:3b"}',
            '{"X-Emb":"1"}',
        )
        self.assertIn('"X-Test": "1"', headers)
        self.assertIn('"mini": "qwen2.5:3b"', routes)
        self.assertIn('"X-Emb": "1"', emb)

    def test_prettify_llm_json_texts_invalid_keeps_original(self):
        bad = "{bad json}"
        headers, routes, emb = dash_app.prettify_llm_json_texts(bad, bad, bad)
        self.assertEqual(headers, bad)
        self.assertEqual(routes, bad)
        self.assertEqual(emb, bad)

    def test_chat_api_base_and_headers(self):
        cfg = {"api": {"host": "127.0.0.1", "port": 8976, "api_key": "k"}}
        with patch("dash_ui.app.load_config", return_value=cfg):
            base, headers = dash_app._chat_api_base_and_headers()

        self.assertEqual(base, "http://127.0.0.1:8976")
        self.assertEqual(headers["api_key"], "k")

    def test_check_api_health_success(self):
        cfg = {"api": {"host": "127.0.0.1", "port": 8976, "api_key": "k"}}
        mock_resp = Mock()
        mock_resp.raise_for_status.return_value = None
        with patch("dash_ui.app.load_config", return_value=cfg), patch("dash_ui.app.requests.get", return_value=mock_resp):
            result = dash_app.check_api_health(0)

        self.assertEqual(result, dash_app.no_update)

    def test_check_api_health_failed(self):
        cfg = {"api": {"host": "127.0.0.1", "port": 8976, "api_key": "k"}}
        with patch("dash_ui.app.load_config", return_value=cfg), patch("dash_ui.app.requests.get", side_effect=Exception("down")):
            alert = dash_app.check_api_health(0)

        self.assertEqual(alert.color, "danger")
        self.assertIn("API 未連線", str(alert.children))
        self.assertIn("http://127.0.0.1:8976", str(alert.children))

    def test_render_chat_messages(self):
        rows = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi"},
        ]
        nodes = dash_app.render_chat_messages(rows)
        self.assertEqual(len(nodes), 2)

    def test_format_embedding_test_result(self):
        text = dash_app.format_embedding_test_result(
            {
                "model": "text-embedding-qwen3-embedding-0.6b",
                "endpoint": "http://127.0.0.1:1234/v1/embeddings",
                "dimension": 1024,
                "usage": {"prompt_tokens": 8, "total_tokens": 8},
            }
        )
        self.assertIn("dimension: 1024", text)
        self.assertIn("prompt_tokens", text)

    def test_test_embedding_connectivity_success(self):
        cfg = {"api": {"host": "127.0.0.1", "port": 8976, "api_key": "k"}}
        mock_resp = Mock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {
            "model": "text-embedding-qwen3-embedding-0.6b",
            "endpoint": "http://127.0.0.1:1234/v1/embeddings",
            "dimension": 1024,
            "usage": {"prompt_tokens": 8, "total_tokens": 8},
        }
        with patch("dash_ui.app.load_config", return_value=cfg), patch("dash_ui.app.requests.post", return_value=mock_resp):
            alert = dash_app.test_embedding_connectivity(1)
        self.assertEqual(alert.color, "success")

    def test_test_embedding_connectivity_failed(self):
        cfg = {"api": {"host": "127.0.0.1", "port": 8976, "api_key": "k"}}
        with patch("dash_ui.app.load_config", return_value=cfg), patch("dash_ui.app.requests.post", side_effect=Exception("boom")):
            alert = dash_app.test_embedding_connectivity(1)
        self.assertEqual(alert.color, "danger")

    def test_router_registry_editor(self):
        node = dash_app.router("/registry-editor")
        self.assertIsNotNone(node)

    def test_validate_registry_source_success(self):
        source = """
def sample_tool():
    return 1

RPA_REGISTRY = {
    "sample_tool": {"func": sample_tool, "desc": "ok", "params": []}
}
"""
        ok, message = dash_app.validate_registry_source(source)
        self.assertTrue(ok)
        self.assertIn("通過", message)

    def test_validate_registry_source_failed(self):
        source = "RPA_REGISTRY = []"
        ok, message = dash_app.validate_registry_source(source)
        self.assertFalse(ok)
        self.assertIn("dict", message)

    def test_atomic_write_registry_source(self):
        with TemporaryDirectory() as tmp_dir:
            base_dir = Path(tmp_dir)
            core_dir = base_dir / "core"
            core_dir.mkdir(parents=True)
            target = core_dir / "registry.py"
            target.write_text("a=1", encoding="utf-8")

            with patch.object(dash_app, "BASE_DIR", base_dir):
                dash_app.atomic_write_registry_source("x = 2")

            self.assertEqual(target.read_text(encoding="utf-8"), "x = 2")

    def test_backup_registry_file(self):
        with TemporaryDirectory() as tmp_dir:
            base_dir = Path(tmp_dir)
            core_dir = base_dir / "core"
            core_dir.mkdir(parents=True)
            (core_dir / "registry.py").write_text("a=1", encoding="utf-8")

            with patch.object(dash_app, "BASE_DIR", base_dir):
                backup = dash_app.backup_registry_file()

            self.assertTrue(backup.exists())
            self.assertEqual(backup.read_text(encoding="utf-8"), "a=1")


if __name__ == "__main__":
    unittest.main()
