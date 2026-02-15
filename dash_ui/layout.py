import dash_bootstrap_components as dbc
from dash import dcc, html

sidebar = dbc.Col(
    [
        html.Br(),
        html.H5("控制台", className="sidebar-title"),
        html.Hr(),
        dbc.Nav(
            [
                dbc.NavLink("Chat對話", href="/chat", active="exact"),
                dbc.NavLink("系統配置", href="/", active="exact"),
                dbc.NavLink("RPA 列表", href="/rpa-list", active="exact"),
                dbc.NavLink("流程編排", href="/workflow", active="exact"),
                dbc.NavLink("本地 LLM", href="/llm", active="exact"),
                dbc.NavLink("運行日誌", href="/logs", active="exact"),
                dbc.NavLink("注册中心", href="/registry-editor", active="exact"),
            ],
            vertical=True,
            pills=True,
            className="sidebar-nav",
        ),
    ],
    width=2,
    className="app-sidebar",
)

main_layout = html.Div(
    [
        dcc.Store(id="log-context-lines-store", data=5, storage_type="session"),
        dcc.Interval(id="api-health-poll", interval=15000, n_intervals=0),
        dbc.Row(
            [
                sidebar,
                dbc.Col(
                    [
                        html.Div(id="api-health-status", className="status-area p-2"),
                        html.Div(id="page-content", className="page-content-wrap"),
                    ],
                    width=10,
                    className="app-content",
                ),
            ],
            className="g-0 app-shell-row",
        ),
    ],
    className="app-shell",
)
