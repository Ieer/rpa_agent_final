import dash_bootstrap_components as dbc
from dash import html
import json

from dash_ui.utils import load_config


def layout():
    cfg = load_config()
    llm = cfg["llm"]
    embedding = cfg.get("embedding", {})
    providers = [
        {"label": "custom", "value": "custom"},
        {"label": "openrouter", "value": "openrouter"},
        {"label": "openai", "value": "openai"},
        {"label": "anthropic", "value": "anthropic"},
        {"label": "dashscope", "value": "dashscope"},
        {"label": "moonshot", "value": "moonshot"},
        {"label": "deepseek", "value": "deepseek"},
        {"label": "vllm", "value": "vllm"},
    ]

    return dbc.Container(
        [
            html.Div([html.H5("本地 LLM 配置", className="page-title")], className="page-header"),
            html.H6("核心設定", className="section-title"),
            dbc.Row(
                [
                    dbc.Col([dbc.Label("Base URL"), dbc.Input(id="llm-base-url", value=llm.get("base_url", ""))], md=6),
                    dbc.Col([dbc.Label("模型"), dbc.Input(id="llm-model", value=llm.get("model", ""))], md=6),
                ],
                className="mb-3",
            ),
            dbc.Row(
                [
                    dbc.Col([dbc.Label("Provider"), dbc.Select(id="llm-provider", options=providers, value=llm.get("provider", "custom"))], md=6),
                    dbc.Col([dbc.Label("API Key"), dbc.Input(id="llm-api-key", value=llm.get("api_key", ""))], md=6),
                ],
                className="mb-3",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Label("Headers (JSON)"),
                            dbc.Textarea(
                                id="llm-headers",
                                value=json.dumps(llm.get("headers", {}), ensure_ascii=False, indent=2),
                                className="input-area-md",
                            ),
                        ],
                        md=6,
                    ),
                    dbc.Col(
                        [
                            dbc.Label("Model Routes (JSON)"),
                            dbc.Textarea(
                                id="llm-model-routes",
                                value=json.dumps(llm.get("model_routes", {}), ensure_ascii=False, indent=2),
                                className="input-area-md",
                            ),
                        ],
                        md=6,
                    ),
                ],
                className="mb-3",
            ),
            dbc.Row(
                [
                    dbc.Col([dbc.Label("Temperature"), dbc.Input(id="llm-temp", type="number", step=0.1, value=llm.get("temperature", 0.1))], md=4),
                    dbc.Col([dbc.Label("Max Tool Iterations"), dbc.Input(id="llm-max-tool-iterations", type="number", value=llm.get("max_tool_iterations", 20))], md=4),
                    dbc.Col([dbc.Label("Memory Window"), dbc.Input(id="llm-memory-window", type="number", value=llm.get("memory_window", 50))], md=4),
                ],
                className="mb-3",
            ),
            html.Hr(),
            html.H5("Embedding 設定", className="section-title"),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Checkbox(
                                id="embedding-enabled",
                                value=bool(embedding.get("enabled", True)),
                                className="me-2",
                            ),
                            dbc.Label("啟用 Embedding", html_for="embedding-enabled", className="d-inline"),
                        ],
                        md=4,
                    ),
                    dbc.Col([dbc.Label("Embedding Base URL"), dbc.Input(id="embedding-base-url", value=embedding.get("base_url", ""))], md=8),
                ],
                className="mb-3",
            ),
            dbc.Row(
                [
                    dbc.Col([dbc.Label("Embedding Model"), dbc.Input(id="embedding-model", value=embedding.get("model", ""))], md=6),
                    dbc.Col([dbc.Label("Embedding API Key"), dbc.Input(id="embedding-api-key", value=embedding.get("api_key", ""))], md=6),
                ],
                className="mb-3",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Label("Embedding Headers (JSON)"),
                            dbc.Textarea(
                                id="embedding-headers",
                                value=json.dumps(embedding.get("headers", {}), ensure_ascii=False, indent=2),
                                className="input-area-md",
                            ),
                        ],
                        md=12,
                    ),
                ],
                className="mb-3",
            ),
            html.Div(
                [
                    dbc.Button("JSON 格式化", id="llm-prettify-btn", color="secondary", className="me-2"),
                    dbc.Button("測試 Embedding 連線", id="embedding-test-btn", color="info", className="me-2"),
                    dbc.Button("保存 LLM 配置", id="llm-save-btn", color="primary"),
                ],
                className="action-row",
            ),
            html.Div(id="embedding-test-result", className="status-area mt-3"),
            html.Div(id="llm-save-result", className="status-area mt-3"),
        ],
        fluid=True,
        className="page-shell p-4",
    )
