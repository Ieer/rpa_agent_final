import json

import dash_bootstrap_components as dbc
from dash import dcc, html

from core.registry import RPA_REGISTRY


def layout():
    options = [{"label": f"{name} | {item['desc']}", "value": name} for name, item in RPA_REGISTRY.items()]
    table_rows = [
        html.Tr([html.Td(name), html.Td(item["desc"]), html.Td(", ".join(item["params"]))])
        for name, item in RPA_REGISTRY.items()
    ]

    return dbc.Container(
        [
            html.Div([html.H5("RPA 列表", className="page-title")], className="page-header"),
            dbc.Table(
                [
                    html.Thead(html.Tr([html.Th("名稱"), html.Th("描述"), html.Th("參數")])),
                    html.Tbody(table_rows),
                ],
                bordered=True,
                striped=True,
                hover=True,
                responsive=True,
                className="professional-table",
            ),
            html.Hr(),
            html.H5("執行 RPA", className="section-title"),
            dcc.Dropdown(id="rpa-run-name", options=options, placeholder="選擇 RPA"), # type: ignore
            dbc.Textarea(id="rpa-run-params", value=json.dumps({}, ensure_ascii=False), className="mt-2 input-area-md"),
            dbc.Button("執行", id="rpa-run-btn", color="success", className="mt-2"),
            html.Pre(id="rpa-run-result", className="mt-3 code-output"),
        ],
        fluid=True,
        className="page-shell p-4",
    )
