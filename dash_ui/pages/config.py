import dash_bootstrap_components as dbc
from dash import dcc, html

from dash_ui.utils import load_config


def layout():
    cfg = load_config()
    return dbc.Container(
        [
            html.Div([html.H5("系統配置", className="page-title")], className="page-header"),
            html.H6("系統設定", className="section-title"),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Label("模式"),
                            dcc.Dropdown(
                                id="cfg-mode",
                                options=[{"label": "skill", "value": "skill"}, {"label": "api", "value": "api"}],
                                value=cfg["system"]["mode"],
                                clearable=False,
                            ),
                        ],
                        md=4,
                    ),
                    dbc.Col(
                        [
                            dbc.Label("最大重試"),
                            dbc.Input(id="cfg-max-retry", type="number", value=cfg["system"]["max_retry"]),
                        ],
                        md=4,
                    ),
                    dbc.Col(
                        [
                            dbc.Label("逾時秒數"),
                            dbc.Input(id="cfg-timeout", type="number", value=cfg["system"]["timeout"]),
                        ],
                        md=4,
                    ),
                ],
                className="mb-3",
            ),
            html.Hr(),
            html.H5("API 設定", className="section-title"),
            dbc.Row(
                [
                    dbc.Col([dbc.Label("API Host"), dbc.Input(id="cfg-api-host", value=cfg["api"]["host"])], md=4),
                    dbc.Col([dbc.Label("API Port"), dbc.Input(id="cfg-api-port", type="number", value=cfg["api"]["port"])], md=4),
                    dbc.Col([dbc.Label("API Key"), dbc.Input(id="cfg-api-key", value=cfg["api"]["api_key"])], md=4),
                ],
                className="mb-3",
            ),
            dbc.Button("保存配置", id="cfg-save", color="primary"),
            html.Div(id="cfg-save-result", className="status-area mt-3"),
        ],
        fluid=True,
        className="page-shell p-4",
    )
