import dash_bootstrap_components as dbc
from dash import dcc, html

from dash_ui.utils import load_config


def layout():
    cfg = load_config()
    chat_cfg = cfg.get("chat", {})
    poll_interval = int(chat_cfg.get("poll_interval_ms", 1200))
    default_session = chat_cfg.get("default_session", "dash:default")

    return dbc.Container(
        [
            html.Div([html.H5("Chat 對話", className="page-title")], className="page-header"),
            dbc.Row(
                [
                    dbc.Col([dbc.Label("Session"), dbc.Input(id="chat-session-key", value=default_session, disabled=True)], md=8),
                    dbc.Col(
                        [
                            dbc.Label("操作"),
                            html.Div(
                                [
                                    dbc.Button("載入歷史", id="chat-history-btn", color="secondary", className="me-2"),
                                    dbc.Button("送出", id="chat-send-btn", color="primary"),
                                ]
                            ),
                        ],
                        md=4,
                    ),
                ],
                className="mb-3",
            ),
            dbc.Textarea(id="chat-input", placeholder="輸入訊息...", className="input-area-sm"),
            html.Div(id="chat-status", className="status-area mt-2"),
            html.Hr(),
            html.Div(id="chat-messages", className="panel-scroll chat-messages"),
            dcc.Store(id="chat-run-id", data=""),
            dcc.Store(id="chat-messages-store", data=[]),
            dcc.Interval(id="chat-poll", interval=poll_interval, n_intervals=0),
        ],
        fluid=True,
        className="page-shell p-4",
    )
