from __future__ import annotations

import ast
import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlencode

import dash_bootstrap_components as dbc
import requests
from dash import Dash, Input, Output, State, callback_context, dcc, html, no_update
from dash.exceptions import MissingCallbackContextException
from flask import has_request_context, request

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.executor import RPAExecutor
from dash_ui.layout import main_layout
from dash_ui.pages import chat, config, llm, logs, registry_editor, rpa_list, workflow
from dash_ui.theme import THEME
from dash_ui.utils import load_config, save_config
from workflow.engine import Workflow

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_MATCH_CONTEXT_LINES = 5
ALLOWED_LOG_CONTEXT_LINES = {3, 5, 10}

ALERT_DEFAULT_DURATION_MS = {
    "success": 1800,
    "info": 1400,
    "warning": 1600,
}


def make_alert(message: Any, color: str = "secondary", *, duration: int | None = None, class_name: str = "app-alert") -> dbc.Alert:
    effective_duration = ALERT_DEFAULT_DURATION_MS.get(color) if duration is None else duration
    return dbc.Alert(message, color=color, duration=effective_duration, className=class_name)

app = Dash(
    __name__,
    external_stylesheets=[THEME],
    assets_folder=str(Path(__file__).resolve().parent / "assets"),
    title="Agent(RPA)控制台",
    suppress_callback_exceptions=True,
)
app.layout = html.Div([dcc.Location(id="url"), main_layout])


@app.callback(Output("page-content", "children"), Input("url", "pathname"))
def router(pathname: str):
    if pathname == "/rpa-list":
        return rpa_list.layout()
    if pathname == "/workflow":
        return workflow.layout()
    if pathname == "/chat":
        return chat.layout()
    if pathname == "/llm":
        return llm.layout()
    if pathname == "/logs":
        return logs.layout()
    if pathname == "/registry-editor":
        return registry_editor.layout()
    return config.layout()


def registry_file_path() -> Path:
    return BASE_DIR / "core" / "registry.py"


def registry_backup_dir_path() -> Path:
    return BASE_DIR / "logs" / "registry_backups"


def load_registry_source() -> str:
    return registry_file_path().read_text(encoding="utf-8")


def is_registry_edit_allowed() -> bool:
    if not has_request_context():
        return True
    remote_addr = (request.remote_addr or "").strip()
    return remote_addr in {"127.0.0.1", "::1", "localhost"}


def validate_registry_source(source: str) -> tuple[bool, str]:
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return False, f"語法錯誤（line {exc.lineno}）: {exc.msg}"

    compile(source, str(registry_file_path()), "exec")

    func_names: set[str] = set()
    registry_assign: ast.Assign | None = None

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_names.add(node.name)
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "RPA_REGISTRY":
                    registry_assign = node

    if registry_assign is None:
        return False, "未找到 RPA_REGISTRY 定義"
    if not isinstance(registry_assign.value, ast.Dict):
        return False, "RPA_REGISTRY 必須是 dict"

    for key_node, value_node in zip(registry_assign.value.keys, registry_assign.value.values):
        if not isinstance(key_node, ast.Constant) or not isinstance(key_node.value, str):
            return False, "RPA_REGISTRY 的 key 必須是字串"
        if not isinstance(value_node, ast.Dict):
            return False, f"RPA {key_node.value} 的設定必須是 dict"

        entry_fields: dict[str, ast.AST] = {}
        for field_key, field_value in zip(value_node.keys, value_node.values):
            if isinstance(field_key, ast.Constant) and isinstance(field_key.value, str):
                entry_fields[field_key.value] = field_value

        for required_key in ("func", "desc", "params"):
            if required_key not in entry_fields:
                return False, f"RPA {key_node.value} 缺少必要欄位: {required_key}"

        func_node = entry_fields["func"]
        if not isinstance(func_node, ast.Name) or func_node.id not in func_names:
            return False, f"RPA {key_node.value} 的 func 必須引用本檔案已定義函式"

        desc_node = entry_fields["desc"]
        if not isinstance(desc_node, ast.Constant) or not isinstance(desc_node.value, str):
            return False, f"RPA {key_node.value} 的 desc 必須是字串"

        params_node = entry_fields["params"]
        if not isinstance(params_node, ast.List):
            return False, f"RPA {key_node.value} 的 params 必須是字串列表"
        for param_node in params_node.elts:
            if not isinstance(param_node, ast.Constant) or not isinstance(param_node.value, str):
                return False, f"RPA {key_node.value} 的 params 必須全部是字串"

    return True, "檢查通過"


def backup_registry_file() -> Path:
    backup_dir = registry_backup_dir_path()
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"registry_{timestamp}.py"
    backup_path.write_text(load_registry_source(), encoding="utf-8")
    return backup_path


def atomic_write_registry_source(source: str) -> None:
    target = registry_file_path()
    with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", dir=str(target.parent), suffix=".tmp") as tmp:
        tmp.write(source)
        temp_name = tmp.name
    Path(temp_name).replace(target)


@app.callback(
    Output("registry-editor-source", "value"),
    Input("url", "pathname"),
    Input("registry-editor-reload", "n_clicks"),
)
def load_registry_source_for_editor(pathname: str, _reload_clicks):
    if pathname != "/registry-editor":
        return no_update
    if not is_registry_edit_allowed():
        return ""
    try:
        return load_registry_source()
    except Exception as exc:
        return f"# 讀取失敗: {exc}"


@app.callback(
    Output("registry-editor-status", "children"),
    Input("registry-editor-check", "n_clicks"),
    Input("registry-editor-save", "n_clicks"),
    State("registry-editor-source", "value"),
    prevent_initial_call=True,
)
def handle_registry_editor_actions(check_clicks, save_clicks, source_text):
    if not is_registry_edit_allowed():
        return make_alert("僅允許 localhost 使用 Registry 編輯功能", color="danger")

    triggered = get_triggered_input_id()
    source = source_text or ""

    if triggered == "registry-editor-check":
        try:
            ok, message = validate_registry_source(source)
            return make_alert(message, color="success" if ok else "danger")
        except Exception as exc:
            return make_alert(f"檢查失敗: {exc}", color="danger")

    if triggered == "registry-editor-save":
        try:
            ok, message = validate_registry_source(source)
            if not ok:
                return make_alert(f"保存失敗：{message}", color="danger")

            backup_path = backup_registry_file()
            atomic_write_registry_source(source)
            return make_alert(
                f"保存成功。備份: {backup_path.name}。請重啟 Dash/UI 與 API 服務使變更生效。",
                color="success",
            )
        except Exception as exc:
            return make_alert(f"保存失敗: {exc}", color="danger")

    return no_update


@app.callback(
    Output("cfg-save-result", "children"),
    Input("cfg-save", "n_clicks"),
    State("cfg-mode", "value"),
    State("cfg-max-retry", "value"),
    State("cfg-timeout", "value"),
    State("cfg-api-host", "value"),
    State("cfg-api-port", "value"),
    State("cfg-api-key", "value"),
    prevent_initial_call=True,
)
def save_system_config(_, mode, max_retry, timeout, api_host, api_port, api_key):
    cfg = load_config()
    cfg["system"]["mode"] = mode
    cfg["system"]["max_retry"] = int(max_retry)
    cfg["system"]["timeout"] = int(timeout)
    cfg["api"]["host"] = api_host
    cfg["api"]["port"] = int(api_port)
    cfg["api"]["api_key"] = api_key
    save_config(cfg)
    return make_alert("系統配置已保存", color="success", duration=2000)


@app.callback(
    Output("rpa-run-result", "children"),
    Input("rpa-run-btn", "n_clicks"),
    State("rpa-run-name", "value"),
    State("rpa-run-params", "value"),
    prevent_initial_call=True,
)
def run_single_rpa(_, rpa_name, params_text):
    if not rpa_name:
        return "請先選擇 RPA"
    try:
        params = json.loads(params_text or "{}")
        result = RPAExecutor.run(rpa_name, params)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as exc:
        return f"執行失敗: {exc}"


@app.callback(
    Output("workflow-run-result", "children"),
    Input("workflow-run-btn", "n_clicks"),
    State("workflow-input", "value"),
    prevent_initial_call=True,
)
def run_workflow(_, workflow_text):
    try:
        task_list = json.loads(workflow_text)
        if not isinstance(task_list, list):
            return "輸入必須是 list JSON"
        for task in task_list:
            if not isinstance(task, dict) or not task.get("name"):
                return "每個任務必須是包含 name 的 JSON object"
        result = Workflow.run(task_list)
        return render_workflow_result(result)
    except Exception as exc:
        return f"流程執行失敗: {exc}"


def _workflow_status_color(status: str) -> str:
    if status == "success":
        return "success"
    if status == "failed":
        return "danger"
    return "secondary"


def render_workflow_result(steps: list[dict]) -> dbc.Container:
    if not steps:
        return dbc.Container([make_alert("沒有可執行的任務", color="warning")], fluid=True, className="px-0")

    run_id = steps[0].get("run_id", "")
    success_count = sum(1 for step in steps if step.get("status") == "success")
    failed_count = sum(1 for step in steps if step.get("status") == "failed")
    total_duration = sum(int(step.get("duration_ms", 0) or 0) for step in steps)

    cards = []
    for step in steps:
        status = str(step.get("status", "unknown"))
        step_id = str(step.get("step_id", "-") or "-")
        step_logs_query = urlencode({"run_id": run_id, "step_id": step_id})
        header = html.Div(
            [
                html.Span(f"Step {step.get('step_index', '?')} · {step.get('name', '-')}", className="fw-semibold"),
                dbc.Badge(status, color=_workflow_status_color(status), className="ms-2"),
            ],
            className="d-flex align-items-center",
        )

        details: list[Any] = [
            html.Div(
                [
                    html.Span("step_id: ", className="small text-muted"),
                    html.A(step_id, href=f"/logs?{step_logs_query}", className="small"),
                ]
            ),
            html.Div(f"duration: {step.get('duration_ms', 0)} ms", className="small text-muted"),
            html.Div(f"started_at: {step.get('started_at', '-')}", className="small text-muted"),
        ]

        error_message = step.get("error_message")
        if error_message:
            details.append(make_alert(f"error: {error_message}", color="danger", class_name="mt-2 mb-0 py-2 app-alert"))

        cards.append(dbc.Card([dbc.CardHeader(header), dbc.CardBody(details)], className="mb-2"))

    return dbc.Container(
        [
            make_alert(
                f"run_id: {run_id}｜總步驟: {len(steps)}｜成功: {success_count}｜失敗: {failed_count}｜總耗時: {total_duration} ms",
                color="info",
                class_name="mb-3 app-alert",
            ),
            dbc.Button("查看本次流程日誌", href=f"/logs?run_id={run_id}", color="info", outline=True, className="mb-3"),
            *cards,
        ],
        fluid=True,
        className="px-0",
    )


def _chat_api_base_and_headers() -> tuple[str, dict[str, str]]:
    cfg = load_config()
    api = cfg["api"]
    base = f"http://{api['host']}:{api['port']}"
    headers = {"api_key": api["api_key"]}
    return base, headers


@app.callback(
    Output("api-health-status", "children"),
    Input("api-health-poll", "n_intervals"),
)
def check_api_health(_):
    base_url, headers = _chat_api_base_and_headers()
    try:
        response = requests.get(
            f"{base_url}/api/rpa/list",
            headers=headers,
            timeout=3,
        )
        response.raise_for_status()
        return no_update
    except Exception:
        return make_alert(
            [
                "API 未連線：Dash Chat 無法取得回覆。",
                html.Br(),
                f"目前 API 位址：{base_url}",
                html.Br(),
                "請確認已啟動後端（python start.py）且 config.yaml 的 system.mode 設為 api。",
            ],
            color="danger",
            duration=None,
            class_name="mb-2 app-alert",
        )


def render_chat_messages(messages: list[dict]) -> list:
    nodes = []
    for item in messages:
        role = item.get("role", "assistant")
        content = item.get("content", "")
        color = "primary" if role == "user" else "dark"
        title = "你" if role == "user" else "Agent"
        nodes.append(
            dbc.Card(
                [
                    dbc.CardHeader(title),
                    dbc.CardBody(html.Pre(content, style={"whiteSpace": "pre-wrap", "marginBottom": 0})),
                ],
                color=color,
                outline=True,
                className="mb-2",
            )
        )
    return nodes


def format_embedding_test_result(payload: dict) -> str:
    model = payload.get("model", "")
    endpoint = payload.get("endpoint", "")
    dimension = payload.get("dimension")
    usage = payload.get("usage")
    usage_text = json.dumps(usage, ensure_ascii=False, indent=2) if usage is not None else "null"
    return (
        f"model: {model}\n"
        f"endpoint: {endpoint}\n"
        f"dimension: {dimension}\n"
        f"usage: {usage_text}"
    )


@app.callback(
    Output("chat-run-id", "data"),
    Output("chat-input", "value"),
    Output("chat-status", "children"),
    Output("chat-messages-store", "data"),
    Input("chat-send-btn", "n_clicks"),
    Input("chat-history-btn", "n_clicks"),
    Input("chat-poll", "n_intervals"),
    State("chat-run-id", "data"),
    State("chat-input", "value"),
    State("chat-session-key", "value"),
    State("chat-messages-store", "data"),
    prevent_initial_call=True,
)
def chat_controller(send_clicks, history_clicks, _, run_id, chat_input, session_key, messages):
    messages = messages or []
    triggered = callback_context.triggered[0]["prop_id"].split(".")[0] if callback_context.triggered else ""

    base_url, headers = _chat_api_base_and_headers()

    if triggered == "chat-send-btn":
        text = (chat_input or "").strip()
        if not text:
            return run_id or "", no_update, make_alert("請輸入訊息", color="warning", duration=1500), messages

        try:
            response = requests.post(
                f"{base_url}/api/chat/send",
                json={"message": text, "session_key": session_key},
                headers=headers,
                timeout=20,
            )
            response.raise_for_status()
            payload = response.json()
            new_run = payload["run_id"]
            new_messages = [*messages, {"role": "user", "content": text}]
            return new_run, "", make_alert("訊息已送出，等待回覆...", color="info", duration=1200), new_messages
        except Exception as exc:
            return run_id or "", chat_input, make_alert(f"送出失敗: {exc}", color="danger"), messages

    if triggered == "chat-history-btn":
        try:
            response = requests.get(
                f"{base_url}/api/chat/history",
                params={"session_key": session_key, "limit": 50},
                headers=headers,
                timeout=20,
            )
            response.raise_for_status()
            payload = response.json()
            rows = payload.get("data", [])
            return run_id or "", no_update, make_alert("歷史已載入", color="secondary", duration=1200), rows
        except Exception as exc:
            return run_id or "", no_update, make_alert(f"載入歷史失敗: {exc}", color="danger"), messages

    if triggered == "chat-poll":
        if not run_id:
            return "", no_update, no_update, messages

        try:
            response = requests.get(
                f"{base_url}/api/chat/status/{run_id}",
                headers=headers,
                timeout=20,
            )
            response.raise_for_status()
            payload = response.json().get("data", {})
            status = payload.get("status")
            if status in {"queued", "running"}:
                return run_id, no_update, make_alert(f"回覆中（{status}）...", color="secondary", duration=1000), messages
            if status == "final":
                final_text = payload.get("result") or ""
                new_messages = [*messages, {"role": "assistant", "content": final_text}]
                return "", no_update, make_alert("回覆完成", color="success", duration=1000), new_messages
            if status == "error":
                err = payload.get("error") or "未知錯誤"
                new_messages = [*messages, {"role": "assistant", "content": f"Error: {err}"}]
                return "", no_update, make_alert("回覆失敗", color="danger"), new_messages
            return "", no_update, make_alert("任務不存在", color="warning", duration=1000), messages
        except Exception as exc:
            return run_id, no_update, make_alert(f"輪詢失敗: {exc}", color="danger"), messages

    return run_id or "", no_update, no_update, messages


@app.callback(Output("chat-messages", "children"), Input("chat-messages-store", "data"))
def render_chat_messages_view(messages):
    messages = messages or []
    if not messages:
        return make_alert("尚無對話，請輸入訊息後送出。", color="secondary")
    return render_chat_messages(messages)


@app.callback(
    Output("embedding-test-result", "children"),
    Input("embedding-test-btn", "n_clicks"),
    prevent_initial_call=True,
)
def test_embedding_connectivity(_):
    base_url, headers = _chat_api_base_and_headers()
    try:
        response = requests.post(
            f"{base_url}/api/embedding/test",
            json={"input_text": "embedding test from dash"},
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        detail = format_embedding_test_result(payload)
        return make_alert(html.Pre(detail, style={"whiteSpace": "pre-wrap", "marginBottom": 0}), color="success")
    except Exception as exc:
        return make_alert(f"Embedding 測試失敗: {exc}", color="danger")


def prettify_llm_json_texts(
    headers_text: str | None,
    model_routes_text: str | None,
    embedding_headers_text: str | None,
) -> tuple[str, str, str]:
    def _prettify(text: str | None) -> str:
        if not text:
            return "{}"
        try:
            obj = json.loads(text)
            if isinstance(obj, dict):
                return json.dumps(obj, ensure_ascii=False, indent=2)
            return text
        except json.JSONDecodeError:
            return text

    return _prettify(headers_text), _prettify(model_routes_text), _prettify(embedding_headers_text)


@app.callback(
    Output("llm-headers", "value"),
    Output("llm-model-routes", "value"),
    Output("embedding-headers", "value"),
    Input("llm-prettify-btn", "n_clicks"),
    State("llm-headers", "value"),
    State("llm-model-routes", "value"),
    State("embedding-headers", "value"),
    prevent_initial_call=True,
)
def prettify_llm_json(_, headers_text, model_routes_text, embedding_headers_text):
    return prettify_llm_json_texts(headers_text, model_routes_text, embedding_headers_text)


@app.callback(
    Output("llm-save-result", "children"),
    Input("llm-save-btn", "n_clicks"),
    State("llm-base-url", "value"),
    State("llm-model", "value"),
    State("llm-provider", "value"),
    State("llm-api-key", "value"),
    State("llm-headers", "value"),
    State("llm-model-routes", "value"),
    State("llm-temp", "value"),
    State("llm-max-tool-iterations", "value"),
    State("llm-memory-window", "value"),
    State("embedding-enabled", "value"),
    State("embedding-base-url", "value"),
    State("embedding-model", "value"),
    State("embedding-api-key", "value"),
    State("embedding-headers", "value"),
    prevent_initial_call=True,
)
def save_llm_config(
    _,
    base_url,
    model,
    provider,
    api_key,
    headers_text,
    model_routes_text,
    temperature,
    max_tool_iterations,
    memory_window,
    embedding_enabled,
    embedding_base_url,
    embedding_model,
    embedding_api_key,
    embedding_headers_text,
):
    cfg = load_config()

    try:
        headers = json.loads(headers_text or "{}")
        model_routes = json.loads(model_routes_text or "{}")
        embedding_headers = json.loads(embedding_headers_text or "{}")
    except json.JSONDecodeError as exc:
        return make_alert(f"JSON 格式錯誤: {exc}", color="danger")

    if not isinstance(headers, dict):
        return make_alert("Headers 必須是 JSON object", color="danger")
    if not isinstance(model_routes, dict):
        return make_alert("Model Routes 必須是 JSON object", color="danger")
    if not isinstance(embedding_headers, dict):
        return make_alert("Embedding Headers 必須是 JSON object", color="danger")

    cfg["llm"]["base_url"] = base_url
    cfg["llm"]["model"] = model
    cfg["llm"]["provider"] = provider
    cfg["llm"]["api_key"] = api_key
    cfg["llm"]["temperature"] = float(temperature)
    cfg["llm"]["headers"] = headers
    cfg["llm"]["model_routes"] = model_routes
    cfg["llm"]["max_tool_iterations"] = int(max_tool_iterations)
    cfg["llm"]["memory_window"] = int(memory_window)
    cfg["embedding"] = {
        "enabled": bool(embedding_enabled),
        "base_url": embedding_base_url,
        "model": embedding_model,
        "api_key": embedding_api_key,
        "headers": embedding_headers,
    }
    save_config(cfg)
    return make_alert("LLM 配置已保存", color="success", duration=2000)


def parse_run_id_from_search(search: str | None) -> str:
    if not search:
        return ""
    query = search[1:] if search.startswith("?") else search
    values = parse_qs(query).get("run_id", [])
    return values[0].strip() if values else ""


def parse_step_id_from_search(search: str | None) -> str:
    if not search:
        return ""
    query = search[1:] if search.startswith("?") else search
    values = parse_qs(query).get("step_id", [])
    return values[0].strip() if values else ""


def build_filtered_log_text(lines: list[str], run_id: str, step_id: str) -> str:
    if not run_id and not step_id:
        return "\n".join(lines[-30:])

    filtered = lines
    if run_id:
        filtered = [line for line in filtered if run_id in line]
    if step_id:
        filtered = [line for line in filtered if step_id in line]

    if not filtered:
        if run_id and step_id:
            return f"查無 run_id={run_id} step_id={step_id} 對應日誌"
        if run_id:
            return f"查無 run_id={run_id} 對應日誌"
        return f"查無 step_id={step_id} 對應日誌"

    return "\n".join(filtered[-100:])


def build_filtered_log_lines(lines: list[str], run_id: str, step_id: str) -> list[str]:
    filtered = lines
    if run_id:
        filtered = [line for line in filtered if run_id in line]
    if step_id:
        filtered = [line for line in filtered if step_id in line]

    if run_id or step_id:
        return filtered[-100:]
    return lines[-30:]


def clamp_match_index(index: int, match_total: int) -> int:
    if match_total <= 0:
        return 0
    if index < 0:
        return 0
    if index >= match_total:
        return match_total - 1
    return index


def next_match_index(current: int, match_total: int, direction: int) -> int:
    if match_total <= 0:
        return 0
    return (current + direction) % match_total


def build_log_nodes(display_lines: list[str], step_id: str, active_match_line_index: int) -> list[Any]:
    if not step_id:
        return ["\n".join(display_lines)]

    nodes: list[Any] = []
    for line_index, line in enumerate(display_lines):
        text = f"{line}\n"
        if step_id in line:
            if line_index == active_match_line_index:
                nodes.append(html.Mark(f"▶ {text}", className="p-0"))
            else:
                nodes.append(html.Mark(f"  {text}", className="p-0"))
        else:
            nodes.append(text)
    return nodes


def move_active_line_to_top(display_lines: list[str], active_line_index: int) -> tuple[list[str], int]:
    if active_line_index < 0 or active_line_index >= len(display_lines):
        return display_lines, active_line_index
    reordered = [*display_lines[active_line_index:], *display_lines[:active_line_index]]
    return reordered, 0


def pin_active_line_with_context(
    display_lines: list[str], active_line_index: int, context_lines: int = LOG_MATCH_CONTEXT_LINES
) -> tuple[list[str], int]:
    if active_line_index < 0 or active_line_index >= len(display_lines):
        return display_lines, active_line_index

    context = max(int(context_lines), 0)
    start = max(0, active_line_index - context)
    end = min(len(display_lines), active_line_index + context + 1)

    before_lines = display_lines[start:active_line_index]
    after_lines = display_lines[active_line_index + 1 : end]
    focused = [display_lines[active_line_index], *before_lines, *after_lines]
    return focused, 0


def get_triggered_input_id() -> str:
    try:
        return callback_context.triggered[0]["prop_id"].split(".")[0] if callback_context.triggered else ""
    except MissingCallbackContextException:
        return ""


def normalize_log_context_lines(value: Any) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return LOG_MATCH_CONTEXT_LINES
    return parsed if parsed in ALLOWED_LOG_CONTEXT_LINES else LOG_MATCH_CONTEXT_LINES


@app.callback(
    Output("log-context-lines-store", "data"),
    Input("log-context-lines", "value"),
    State("log-context-lines-store", "data"),
)
def persist_log_context_lines(value, current_store_value):
    normalized = normalize_log_context_lines(value)
    if normalized == normalize_log_context_lines(current_store_value):
        return no_update
    return normalized


@app.callback(
    Output("log-filter-run-id", "value"),
    Output("log-filter-step-id", "value"),
    Output("log-context-lines", "value"),
    Input("url", "pathname"),
    Input("url", "search"),
    State("log-context-lines-store", "data"),
)
def sync_log_filter_from_url(pathname: str, search: str, context_lines_store: Any):
    if pathname != "/logs":
        return no_update, no_update, no_update
    return (
        parse_run_id_from_search(search),
        parse_step_id_from_search(search),
        normalize_log_context_lines(context_lines_store),
    )


@app.callback(
    Output("log-content", "children"),
    Output("log-filter-hint", "children"),
    Output("log-match-index", "data"),
    Output("log-match-counter", "children"),
    Output("log-prev-match", "disabled"),
    Output("log-next-match", "disabled"),
    Input("log-refresh", "n_intervals"),
    Input("log-filter-run-id", "value"),
    Input("log-filter-step-id", "value"),
    Input("log-context-lines", "value"),
    Input("log-prev-match", "n_clicks"),
    Input("log-next-match", "n_clicks"),
    State("url", "search"),
    State("log-match-index", "data"),
)
def refresh_logs(_, run_id, step_id, context_lines, prev_clicks, next_clicks, search, current_match_index):
    triggered = get_triggered_input_id()
    log_file = BASE_DIR / load_config()["rpa"]["log_file"]
    if not log_file.exists():
        return "尚無日誌", "目前顯示：全部", 0, "step_id 命中: 0/0", True, True

    lines = log_file.read_text(encoding="utf-8", errors="ignore").splitlines()
    effective_run_id = (run_id or parse_run_id_from_search(search) or "").strip()
    effective_step_id = (step_id or parse_step_id_from_search(search) or "").strip()

    if effective_run_id and effective_step_id:
        hint = f"目前篩選 run_id: {effective_run_id}｜step_id: {effective_step_id}"
    elif effective_run_id:
        hint = f"目前篩選 run_id: {effective_run_id}"
    elif effective_step_id:
        hint = f"目前篩選 step_id: {effective_step_id}"
    else:
        hint = "目前顯示：全部"

    display_lines = build_filtered_log_lines(lines, effective_run_id, effective_step_id)
    if not display_lines:
        empty_text = build_filtered_log_text(lines, effective_run_id, effective_step_id)
        return empty_text, hint, 0, "step_id 命中: 0/0", True, True

    match_line_indexes = [index for index, line in enumerate(display_lines) if effective_step_id and effective_step_id in line]
    match_total = len(match_line_indexes)

    current_index = int(current_match_index or 0)
    if triggered == "log-prev-match":
        current_index = next_match_index(current_index, match_total, -1)
    elif triggered == "log-next-match":
        current_index = next_match_index(current_index, match_total, 1)
    else:
        current_index = clamp_match_index(current_index, match_total)

    active_line_index = match_line_indexes[current_index] if match_total > 0 else -1
    if triggered in {"log-prev-match", "log-next-match"} and active_line_index >= 0:
        selected_context_lines = normalize_log_context_lines(context_lines)
        display_lines, active_line_index = pin_active_line_with_context(
            display_lines,
            active_line_index,
            context_lines=selected_context_lines,
        )

    log_nodes = build_log_nodes(display_lines, effective_step_id, active_line_index)
    counter = f"step_id 命中: {current_index + 1}/{match_total}" if match_total > 0 else "step_id 命中: 0/0"
    disable_nav = match_total <= 1

    return log_nodes, hint, current_index, counter, disable_nav, disable_nav


def run() -> None:
    app.run(host="127.0.0.1", port=8050, debug=False, use_reloader=False)
