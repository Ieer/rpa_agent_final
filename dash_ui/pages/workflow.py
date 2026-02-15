import json

import dash_bootstrap_components as dbc
from dash import html


def layout():
    sample = [
        {"name": "open_notepad", "params": {}},
        {"name": "type_text", "params": {"text": "Hello from workflow"}},
    ]
    return dbc.Container(
        [
            html.Div([html.H5("流程編排", className="page-title")], className="page-header"),
            dbc.Label("任務 JSON（list）"),
            dbc.Textarea(
                id="workflow-input",
                value=json.dumps(sample, ensure_ascii=False, indent=2),
                className="input-area-lg",
            ),
            dbc.Button("執行流程", id="workflow-run-btn", color="warning", className="mt-2"),
            html.Div(id="workflow-run-result", className="status-area mt-3"),
        ],
        fluid=True,
        className="page-shell p-4",
    )
