import dash_bootstrap_components as dbc
from dash import dcc, html


def layout():
    return dbc.Container(
        [
            html.Div([html.H5("運行日誌", className="page-title")], className="page-header"),
            dcc.Store(id="log-match-index", data=0),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Input(
                            id="log-filter-run-id",
                            placeholder="輸入 run_id 篩選日誌",
                            type="text",
                            debounce=True,
                        ),
                        md=4,
                    ),
                    dbc.Col(
                        dbc.Input(
                            id="log-filter-step-id",
                            placeholder="輸入 step_id 篩選日誌",
                            type="text",
                            debounce=True,
                        ),
                        md=4,
                    ),
                    dbc.Col(html.Div(id="log-filter-hint", className="compact-muted mt-2"), md=4),
                ],
                className="mb-2",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dcc.Dropdown(
                            id="log-context-lines",
                            options=[
                                {"label": "前後 3 行", "value": 3},
                                {"label": "前後 5 行", "value": 5},
                                {"label": "前後 10 行", "value": 10},
                            ],
                            value=5,
                            clearable=False,
                        ),
                        md=3,
                    ),
                    dbc.Col(
                        dbc.ButtonGroup(
                            [
                                dbc.Button("上一筆命中", id="log-prev-match", color="secondary", outline=True),
                                dbc.Button("下一筆命中", id="log-next-match", color="secondary", outline=True),
                            ]
                        ),
                        md=3,
                    ),
                    dbc.Col(html.Div(id="log-match-counter", className="compact-muted mt-2"), md=6),
                ],
                className="mb-2",
            ),
            dcc.Interval(id="log-refresh", interval=3000, n_intervals=0),
            html.Pre(id="log-content", className="log-view"),
        ],
        fluid=True,
        className="page-shell p-4",
    )
