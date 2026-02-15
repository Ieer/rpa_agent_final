import dash_bootstrap_components as dbc
from dash import dcc, html


def layout():
    return dbc.Container(
        [
            html.Div([html.H5("Registry 編輯器（MVP）", className="page-title")], className="page-header"),
            dbc.Alert(
                "僅限本機使用。保存前會先做語法與結構檢查，並自動備份。保存後需重啟服務才會生效。",
                color="warning",
                className="mb-3 app-alert",
            ),
            dbc.ButtonGroup(
                [
                    dbc.Button("重新載入", id="registry-editor-reload", color="secondary", outline=True),
                    dbc.Button("檢查語法/結構", id="registry-editor-check", color="info", outline=True),
                    dbc.Button("保存", id="registry-editor-save", color="danger"),
                ],
                className="mb-3",
            ),
            html.Div(id="registry-editor-status", className="status-area mb-3"),
            dcc.Textarea(
                id="registry-editor-source",
                value="",
                className="editor-area",
            ),
        ],
        fluid=True,
        className="page-shell p-4",
    )
