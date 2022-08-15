import os
import pathlib

import dash
import plotly.graph_objs as go
import dash_daq as daq
from dash.exceptions import PreventUpdate
from dash import ALL, dash_table, html, dcc, MATCH, Output, Input, State
import numpy as np
import pandas as pd
import boto3

app = dash.Dash(
    __name__,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}]
)
app.title = "Crypto Trading Dashboard"
server = app.server
app.config["suppress_callback_exceptions"] = True

APP_PATH = str(pathlib.Path(__file__).parent.resolve())
df = pd.read_csv(os.path.join(APP_PATH, os.path.join("data", "spc_data.csv")))

params = list(df)
# print(params)
max_length = len(df)
# print(max_length)

suffix_row = "_row"
suffix_button_id = "_button"
suffix_sparkline_graph = "_sparkline_graph"
suffix_count = "_count"
suffix_ooc_n = "_OOC_number"
suffix_ooc_g = "_OOC_graph"
suffix_indicator = "_indicator"


def build_banner():
    return html.Div(
        id="banner",
        className="banner",
        children=[
            html.Div(
                id="banner-text",
                children=[
                    html.H5("Crypto Simulation Dashboard"),
                    html.H6("Real-time Cryptocurrency Reporting"),
                ],
            ),
            html.Div(
                id="banner-logo",
                children=[
                    html.Button(
                        id="dashboard-button", children="DASHBOARD", n_clicks=0
                    ),
                    html.Button(
                        id="settings-button", children="SETTINGS", n_clicks=0
                    ),
                    html.A(
                        html.Img(id="logo", src=app.get_asset_url("dash-logo-new.png")),
                        href="https://plotly.com/dash/",
                    ),
                ],
            ),
        ],
    )


# def build_tabs():
#     return html.Div(
#         id="tabs",
#         className="tabs",
#         children=[
#             dcc.Tabs(
#                 id="app-tabs",
#                 value="tab2",
#                 className="custom-tabs",
#                 children=[
#                     dcc.Tab(
#                         id="Specs-tab",
#                         label="Specification Settings",
#                         value="tab1",
#                         className="custom-tab",
#                         selected_className="custom-tab--selected",
#                     ),
#                     dcc.Tab(
#                         id="Control-chart-tab",
#                         label="Control Charts Dashboard",
#                         value="tab2",
#                         className="custom-tab",
#                         selected_className="custom-tab--selected",
#                     ),
#                 ],
#             )
#         ],
#     )


def init_df():
    ret = {}
    for col in list(df[1:]):
        data = df[col]
        stats = data.describe()

        std = stats["std"].tolist()
        ucl = (stats["mean"] + 3 * stats["std"]).tolist()
        lcl = (stats["mean"] - 3 * stats["std"]).tolist()
        usl = (stats["mean"] + stats["std"]).tolist()
        lsl = (stats["mean"] - stats["std"]).tolist()

        ret.update(
            {
                col: {
                    "data": data,
                    "mean": stats["mean"].tolist(),
                    "std": std,
                    "ucl": round(ucl, 3),
                    "lcl": round(lcl, 3),
                    "usl": round(usl, 3),
                    "lsl": round(lsl, 3),
                    "min": stats["min"].tolist(),
                    "max": stats["max"].tolist(),
                    "ooc": populate_ooc(data, ucl, lcl),
                }
            }
        )

    return ret


def populate_ooc(data, ucl, lcl):
    ooc_count = 0
    ret = []
    for i in range(len(data)):
        if data[i] >= ucl or data[i] <= lcl:
            ooc_count += 1
            ret.append(ooc_count / (i + 1))
        else:
            ret.append(ooc_count / (i + 1))
    return ret


state_dict = init_df()


def init_value_setter_store():
    # Initialize store data
    state_dict = init_df()
    return state_dict


def init_owned_currencies_store():
    ret = {}
    for param in params[1:]:
        ret.update(
            {
                param: {
                    "amount": 0,
                    "price": 0
                }
            }
        )

    return ret


def build_tab_1():
    return [
        # Manually select metrics
        html.Div(
            id="set-specs-intro-container",
            # className='twelve columns',
            children=html.P(
                "Select cryptocurrencies of interest, set amount of money and simulate your investment."
            ),
        ),
        html.Div(
            id="settings-menu",
            children=[
                # html.Div(
                #     id="metric-select-menu",
                #     # className='five columns',
                #     children=[
                #         html.Label(id="metric-select-title", children="Select Metrics"),
                #         html.Br(),
                #         dcc.Dropdown(
                #             id="metric-select-dropdown",
                #             options=list(
                #                 {"label": param, "value": param} for param in params[1:]
                #             ),
                #             value=params[1],
                #         ),
                #     ],
                # ),
                html.Div(
                    id="value-setter-menu",
                    # className='six columns',
                    children=[
                        html.Div(id="value-setter-panel", children=[
                                    build_value_setter_line(
                                        "value-setter-panel-header",
                                        "Current Value",
                                        "Set amount in $",
                                        0
                                    )
                                ]),
                        html.Br(),
                        html.Div(
                            id="button-div",
                            children=[
                                html.Button("Add", id="value-adder-btn"),
                                html.Button(
                                    "Remove",
                                    id="value-setter-view-btn",
                                    n_clicks=0,
                                ),
                                html.Button("Confirm", id="value-setter-set-btn"),
                            ],
                        ),
                        html.Div(
                            id="portfolio-str", style={"display": "none"}
                        ),
                        html.Div(
                            id="value-setter-view-output", className="output-datatable"
                        ),
                    ],
                ),
            ],
        ),
    ]


ud_usl_input = daq.NumericInput(
    id="ud_usl_input", className="setting-input", size=200, max=9999999
)
ud_lsl_input = daq.NumericInput(
    id="ud_lsl_input", className="setting-input", size=200, max=9999999
)
ud_ucl_input = daq.NumericInput(
    id="ud_ucl_input", className="setting-input", size=200, max=9999999
)
ud_lcl_input = daq.NumericInput(
    id="ud_lcl_input", className="setting-input", size=200, max=9999999
)


def build_value_setter_line(line_num, value, col3, data_length):
    if line_num.endswith('-header'):
        element = html.Label("Cryptocurrency", className="four columns")
    else:
        element = dcc.Dropdown(
            id={
                'type': 'metric-select-dropdown',
                'index': 'test-{}'.format(data_length)
            },
            options=list(
                {"label": param, "value": param} for param in params[1:]
            ),
            value=params[data_length],
            className="four columns"
        )

    return html.Div(
        id=line_num,
        children=[
            element,
            html.Label(id={
                'type': 'value-div',
                'index': "test-{}".format(data_length)
            }, children=value, className="four columns"),
            html.Div(col3, className="four columns"),
        ],
        className="row",
        style={"margin-bottom": "10px"}
    )


def generate_modal():
    return html.Div(
        id="markdown",
        className="modal",
        children=(
            html.Div(
                id="markdown-container",
                className="markdown-container",
                children=[
                    html.Div(
                        className="close-container",
                        children=html.Button(
                            "Close",
                            id="markdown_close",
                            n_clicks=0,
                            className="closeButton",
                        ),
                    ),
                    html.Div(
                        className="markdown-text",
                        children=dcc.Markdown(
                            children=(
                                """
                        ###### What is this mock app about?

                        This is a dashboard for monitoring real-time process quality along manufacture production line.

                        ###### What does this app shows

                        Click on buttons in `Parameter` column to visualize details of measurement trendlines on the bottom panel.

                        The sparkline on top panel and control chart on bottom panel show Shewhart process monitor using mock data.
                        The trend is updated every other second to simulate real-time measurements. Data falling outside of six-sigma control limit are signals indicating 'Out of Control(OOC)', and will
                        trigger alerts instantly for a detailed checkup.
                        
                        Operators may stop measurement by clicking on `Stop` button, and edit specification parameters by clicking specification tab.

                        ###### Source Code

                        You can find the source code of this app on our [Github repository](https://github.com/plotly/dash-sample-apps/tree/main/apps/dash-manufacture-spc-dashboard).

                    """
                            )
                        ),
                    ),
                ],
            )
        ),
    )


def build_quick_stats_panel(initial_portfolio_value, portfolio_value):
    initial_portfolio_value_str = str(initial_portfolio_value) + "$"

    if len(portfolio_value) == 0:
        portfolio_value_str = "--"
    else:
        portfolio_value_str = str(portfolio_value[-1]) + "$"

    return html.Div(
        id="quick-stats",
        className="row",
        children=[
            html.Div(
                id="card-1",
                children=[
                    html.P(children=[html.Strong("User ID: "), "113"]),
                    html.P(children=[html.Strong("Username: "), "damir1407"]),
                    html.P(children=[html.Strong("Full name: "), "Damir Varešanović"]),
                    html.P(children=[html.Strong("Date: "), "15/08/2022"]),
                ],
            ),
            html.Div(
                id="card-2",
                children=[
                    html.P("Initial portfolio value"),
                    # daq.Gauge(
                    #     id="progress-gauge",
                    #     max=max_length * 2,
                    #     min=0,
                    #     showCurrentValue=True,  # default size 200 pixel
                    # ),
                    html.P(initial_portfolio_value_str, style={'font-size': '40px',
                                                              'align-self': 'center'}),
                    html.P("Current portfolio value"),
                    html.P(id="portfolio-str", children=portfolio_value_str, style={'font-size': '40px',
                                                       'align-self': 'center'}),
                ],
            ),
            html.Div(
                id="utility-card",
                children=[daq.StopButton(id="stop-button", size=160, n_clicks=0)],
            ),
        ],
    )


def generate_section_banner(title):
    return html.Div(className="section-banner", children=title)


def build_top_panel(stopped_interval):
    return html.Div(
        id="top-section-container",
        className="row",
        children=[
            # Metrics summary
            html.Div(
                id="metric-summary-session",
                className="eight columns",
                children=[
                    generate_section_banner("Live Cryptocurrency Values"),
                    html.Div(
                        id="metric-div",
                        children=[
                            generate_metric_list_header(),
                            html.Div(
                                id="metric-rows",
                                children=[
                                    generate_metric_row_helper(stopped_interval, 1),
                                    generate_metric_row_helper(stopped_interval, 2),
                                    generate_metric_row_helper(stopped_interval, 3),
                                    generate_metric_row_helper(stopped_interval, 4),
                                    generate_metric_row_helper(stopped_interval, 5),
                                    generate_metric_row_helper(stopped_interval, 6),
                                    generate_metric_row_helper(stopped_interval, 7),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
            # Piechart
            html.Div(
                id="ooc-piechart-outer",
                className="four columns",
                children=[
                    generate_section_banner("Investment % per Currency"),
                    generate_piechart(),
                ],
            ),
        ],
    )


def generate_piechart():
    return dcc.Graph(
        id="piechart",
        figure={
            "data": [
                {
                    "labels": [],
                    "values": [],
                    "type": "pie",
                    "marker": {"line": {"color": "white", "width": 1}},
                    "hoverinfo": "percent",
                    "textinfo": "label",
                }
            ],
            "layout": {
                "margin": dict(l=20, r=20, t=20, b=20),
                "showlegend": True,
                "paper_bgcolor": "rgba(0,0,0,0)",
                "plot_bgcolor": "rgba(0,0,0,0)",
                "font": {"color": "white"},
                "autosize": True,
            },
        },
    )


# Build header
def generate_metric_list_header():
    return generate_metric_row(
        "metric_header",
        {"height": "3rem", "margin": "1rem 0", "textAlign": "center"},
        {"id": "m_header_1", "children": html.Div("Currency")},
        {"id": "m_header_2", "children": html.Div("Amount")},
        {"id": "m_header_3", "children": html.Div("Sparkline")},
        {"id": "m_header_4", "children": html.Div("Value")},
        # {"id": "m_header_5", "children": html.Div("%OOC")}
    )


def generate_metric_row_helper(stopped_interval, index):
    item = params[index]

    div_id = item + suffix_row
    button_id = item + suffix_button_id
    sparkline_graph_id = item + suffix_sparkline_graph
    count_id = item + suffix_count
    ooc_percentage_id = item + suffix_ooc_n
    # ooc_graph_id = item + suffix_ooc_g
    # indicator_id = item + suffix_indicator

    return generate_metric_row(
        div_id,
        None,
        {
            "id": item,
            "className": "metric-row-button-text",
            "children": html.Button(
                id=button_id,
                className="metric-row-button",
                children=item,
                title="Click to visualize live SPC chart",
                n_clicks=0,
            ),
        },
        {"id": count_id, "children": "0"},
        {
            "id": item + "_sparkline",
            "children": dcc.Graph(
                id=sparkline_graph_id,
                style={"width": "100%", "height": "95%"},
                config={
                    "staticPlot": False,
                    "editable": False,
                    "displayModeBar": False,
                },
                figure=go.Figure(
                    {
                        "data": [
                            {
                                "x": state_dict["Batch"]["data"].tolist()[
                                    :stopped_interval
                                ],
                                "y": state_dict[item]["data"][:stopped_interval],
                                "mode": "lines+markers",
                                "name": item,
                                "line": {"color": "#051C2C"},
                            }
                        ],
                        "layout": {
                            "uirevision": True,
                            "margin": dict(l=0, r=0, t=4, b=4, pad=0),
                            "xaxis": dict(
                                showline=False,
                                showgrid=False,
                                zeroline=False,
                                showticklabels=False,
                            ),
                            "yaxis": dict(
                                showline=False,
                                showgrid=False,
                                zeroline=False,
                                showticklabels=False,
                            ),
                            "paper_bgcolor": "rgba(0,0,0,0)",
                            "plot_bgcolor": "rgba(0,0,0,0)",
                        },
                    }
                ),
            ),
        },
        {"id": ooc_percentage_id, "children": "0.00"},
        # {
        #     "id": item + "_pf",
        #     "children": daq.Indicator(
        #         id=indicator_id, value=True, color="#91dfd2", size=12
        #     ),
        # },
    )


def generate_metric_row(id, style, col1, col2, col3, col4, col5=None):
    if style is None:
        style = {"height": "8rem", "width": "100%"}

    return html.Div(
        id=id,
        className="row metric-row",
        style=style,
        children=[
            html.Div(
                id=col1["id"],
                className="one column",
                style={"margin-right": "2.5rem", "minWidth": "50px"},
                children=col1["children"],
            ),
            html.Div(
                id=col2["id"],
                style={"textAlign": "center"},
                className="one column",
                children=col2["children"],
            ),
            html.Div(
                id=col3["id"],
                style={"height": "100%"},
                className="seven columns",
                children=col3["children"],
            ),
            html.Div(
                id=col4["id"],
                style={"text-align": "center"},
                className="two columns",
                children=col4["children"],
            ),
            # html.Div(
            #     id=col5["id"],
            #     style={"display": "flex", "justifyContent": "center"},
            #     className="one column",
            #     children=col6["children"],
            # ),
        ],
    )


def build_chart_panel():
    return html.Div(
        id="control-chart-container",
        className="twelve columns",
        children=[
            generate_section_banner("Live Portfolio Updates"),
            dcc.Graph(
                id="control-chart-live",
                figure=go.Figure(
                    {
                        "data": [
                            {
                                "x": [],
                                "y": [],
                                "mode": "lines+markers",
                                "name": params[1],
                            }
                        ],
                        "layout": {
                            "paper_bgcolor": "rgba(0,0,0,0)",
                            "plot_bgcolor": "rgba(0,0,0,0)",
                            "xaxis": dict(
                                showline=False, showgrid=False, zeroline=False
                            ),
                            "yaxis": dict(
                                showgrid=False, showline=False, zeroline=False
                            ),
                            "autosize": True,
                        },
                    }
                ),
            ),
        ],
    )


def generate_graph(interval, specs_dict, portfolio_value, initial_portfolio_value):
    if len(portfolio_value) == 0:
        portfolio_value = [initial_portfolio_value]

    portfolio_value = portfolio_value[-50:]
    x_array = list(range(1, len(portfolio_value)+1))
    y_array = portfolio_value

    mean = np.mean(y_array)
    std = np.std(y_array)
    ucl = mean + 2 * std
    lcl = mean - 2 * std

    total_count = 0

    if interval > max_length:
        total_count = max_length - 1
    elif interval > 0:
        total_count = interval

    ooc_trace = {
        "x": [],
        "y": [],
        "name": "High Deviation",
        "mode": "markers",
        "marker": dict(color="rgba(210, 77, 87, 0.7)", symbol="square", size=11),
    }

    for index, data in enumerate(y_array[:total_count]):
        if data >= ucl or data <= lcl:
            ooc_trace["x"].append(index + 1)
            ooc_trace["y"].append(data)

    histo_trace = {
        "x": x_array[:total_count],
        "y": y_array[:total_count],
        "type": "histogram",
        "orientation": "h",
        "name": "Distribution",
        "xaxis": "x2",
        "yaxis": "y2",
        "marker": {"color": "#051C2C"},
    }

    fig = {
        "data": [
            {
                "x": x_array[:total_count],
                "y": y_array[:total_count],
                "mode": "lines+markers",
                "name": "Portfolio Value",
                "line": {"color": "#051C2C"},
            },
            ooc_trace,
            histo_trace,
        ]
    }

    len_figure = len(fig["data"][0]["x"])

    fig["layout"] = dict(
        margin=dict(t=40),
        hovermode="closest",
        uirevision="Portfolio Value",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend={"font": {"color": "darkgray"}, "orientation": "h", "x": 0, "y": 1.1},
        font={"color": "darkgray"},
        showlegend=True,
        xaxis={
            "zeroline": False,
            "showgrid": False,
            "title": "Batch Number",
            "showline": False,
            "domain": [0, 0.8],
            "titlefont": {"color": "darkgray"},
        },
        yaxis={
            "title": "Portfolio Value",
            "showgrid": False,
            "showline": False,
            "zeroline": False,
            "autorange": True,
            "titlefont": {"color": "darkgray"},
        },
        annotations=[
            {
                "x": 0.75,
                "y": lcl,
                "xref": "paper",
                "yref": "y",
                "text": "<b>-2 * STD:" + str(round(lcl, 3)) + "</b>",
                "showarrow": False,
                "font": {"color": "051C2C"},
            },
            {
                "x": 0.75,
                "y": ucl,
                "xref": "paper",
                "yref": "y",
                "text": "<b>2 * STD: " + str(round(ucl, 3)) + "</b>",
                "showarrow": False,
                "font": {"color": "051C2C"},
            },
            # {
            #     "x": 0.75,
            #     "y": usl,
            #     "xref": "paper",
            #     "yref": "y",
            #     "text": "USL: " + str(round(usl, 3)),
            #     "showarrow": False,
            #     "font": {"color": "051C2C"},
            # },
            # {
            #     "x": 0.75,
            #     "y": lsl,
            #     "xref": "paper",
            #     "yref": "y",
            #     "text": "LSL: " + str(round(lsl, 3)),
            #     "showarrow": False,
            #     "font": {"color": "051C2C"},
            # },
            {
                "x": 0.75,
                "y": mean,
                "xref": "paper",
                "yref": "y",
                "text": "<b>Mean: " + str(round(mean, 3)) + "</b>",
                "showarrow": False,
                "font": {"color": "051C2C"},
            },
        ],
        shapes=[
            # {
            #     "type": "line",
            #     "xref": "x",
            #     "yref": "y",
            #     "x0": 1,
            #     "y0": usl,
            #     "x1": len_figure + 1,
            #     "y1": usl,
            #     "line": {"color": "#91dfd2", "width": 1, "dash": "dot"},
            # },
            # {
            #     "type": "line",
            #     "xref": "x",
            #     "yref": "y",
            #     "x0": 1,
            #     "y0": lsl,
            #     "x1": len_figure + 1,
            #     "y1": lsl,
            #     "line": {"color": "#91dfd2", "width": 1, "dash": "dot"},
            # },
            {
                "type": "line",
                "xref": "x",
                "yref": "y",
                "x0": 1,
                "y0": ucl,
                "x1": len_figure + 1,
                "y1": ucl,
                "line": {"color": "rgb(255,127,80)", "width": 1, "dash": "dot"},
            },
            {
                "type": "line",
                "xref": "x",
                "yref": "y",
                "x0": 1,
                "y0": mean,
                "x1": len_figure + 1,
                "y1": mean,
                "line": {"color": "rgb(255,127,80)", "width": 1},
            },
            {
                "type": "line",
                "xref": "x",
                "yref": "y",
                "x0": 1,
                "y0": lcl,
                "x1": len_figure + 1,
                "y1": lcl,
                "line": {"color": "rgb(255,127,80)", "width": 1, "dash": "dot"},
            },
        ],
        xaxis2={
            "title": "Count",
            "domain": [0.8, 1],  # 70 to 100 % of width
            "titlefont": {"color": "darkgray"},
            "showgrid": False,
        },
        yaxis2={
            "anchor": "free",
            "overlaying": "y",
            "side": "right",
            "showticklabels": False,
            "titlefont": {"color": "darkgray"},
        },
    )

    return fig


def update_sparkline(interval, param):
    x_array = state_dict["Batch"]["data"].tolist()
    y_array = state_dict[param]["data"].tolist()

    if interval == 0:
        x_new = y_new = None

    else:
        if interval >= max_length:
            total_count = max_length
        else:
            total_count = interval

        x_new = x_array[:total_count][-1]
        y_new = y_array[:total_count][-1]

    return dict(x=[[x_new]], y=[[y_new]]), [0], 50


def update_count(interval, col, data):
    if interval == 0:
        return "0", "0.00%", 0.00001, "#92e0d3"

    if interval > 0:

        if interval >= max_length:
            total_count = max_length - 1
        else:
            total_count = interval - 1

        # ooc_percentage_f = data[col]["ooc"][total_count] * 100
        ooc_percentage_f = data[col]["data"][total_count]
        ooc_percentage_str = "%.2f" % ooc_percentage_f

        # # Set maximum ooc to 15 for better grad bar display
        # if ooc_percentage_f > 15:
        #     ooc_percentage_f = 15
        #
        # if ooc_percentage_f == 0.0:
        #     ooc_grad_val = 0.00001
        # else:
        #     ooc_grad_val = float(ooc_percentage_f)

        # # Set indicator theme according to threshold 5%
        # if 0 <= ooc_grad_val <= 5:
        #     color = "#92e0d3"
        # elif 5 < ooc_grad_val < 7:
        #     color = "#051C2C"
        # else:
        #     color = "#FF0000"

    return str(total_count + 1), ooc_percentage_str


app.layout = html.Div(
    id="big-app-container",
    children=[
        build_banner(),
        dcc.Interval(
            id="interval-component",
            interval=2000,  # in milliseconds
            n_intervals=1,  # start at batch 50
            disabled=True,
        ),
        html.Div(
            id="app-container",
            children=[
                # build_tabs(),
                # Main app
                html.Div(id="app-content"),
            ],
        ),
        dcc.Store(id="value-setter-store", data=init_value_setter_store()),
        dcc.Store(id="n-interval-stage", data=1),
        dcc.Store(id="portfolio-value", data=[]),
        dcc.Store(id="initial-portfolio-value", data=0),
        dcc.Store(id="owned-currencies", data={}),
        generate_modal(),
    ],
)


@app.callback(
    [Output("app-content", "children"), Output("interval-component", "n_intervals")],
    # [Input("app-tabs", "value")],
    [Input("dashboard-button", "n_clicks"), Input("settings-button", "n_clicks")],
    [State("n-interval-stage", "data"),
     State("initial-portfolio-value", "data"),
     State("portfolio-value", "data")],
)
def render_tab_content(dashboard_button, settings_button, stopped_interval, initial_portfolio_value, portfolio_value):
    ctx = dash.callback_context

    if ctx.triggered:
        prop_id = ctx.triggered[0]["prop_id"].split(".")[0]
        if prop_id == "dashboard-button":
            return (
                html.Div(
                    id="status-container",
                    children=[
                        build_quick_stats_panel(initial_portfolio_value, portfolio_value),
                        html.Div(
                            id="graphs-container",
                            children=[build_top_panel(stopped_interval), build_chart_panel()],
                        ),
                    ],
                ),
                stopped_interval,
            )
        elif prop_id == "settings-button":
            return build_tab_1(), stopped_interval
    else:
        return build_tab_1(), stopped_interval


# Update interval
@app.callback(
    Output("n-interval-stage", "data"),
    # [Input("app-tabs", "value")],
    [Input("settings-button", "n_clicks")],
    [
        State("interval-component", "n_intervals"),
        State("interval-component", "disabled"),
        State("n-interval-stage", "data"),
    ],
)
def update_interval_state(settings_button, cur_interval, disabled, cur_stage):
    if disabled:
        return cur_interval

    ctx = dash.callback_context

    if ctx.triggered:
        prop_id = ctx.triggered[0]["prop_id"].split(".")[0]
        if prop_id == "settings-button":
         return cur_interval
    return cur_stage


# Callbacks for stopping interval update
@app.callback(
    [Output("interval-component", "disabled"), Output("stop-button", "buttonText")],
    [Input("stop-button", "n_clicks")],
    [State("interval-component", "disabled")],
)
def stop_production(n_clicks, current):
    if n_clicks == 0:
        return True, "start"
    return not current, "stop" if current else "start"


# ======= update progress gauge =========
# @app.callback(
#     output=Output("progress-gauge", "value"),
#     inputs=[Input("interval-component", "n_intervals")],
# )
# def update_gauge(interval):
#     if interval < max_length:
#         total_count = interval
#     else:
#         total_count = max_length
#
#     return int(total_count)


@app.callback(
    output=Output("value-setter-panel", "children"),
    inputs=[Input("value-adder-btn", "n_clicks"),
            Input("value-setter-view-btn", "n_clicks")],
    state=[State("value-setter-panel", "children"),
           State("value-setter-store", "data"),
           State("n-interval-stage", "data")],
)
def build_value_setter_panel(add_button, remove_button, settings_children, state_value, cur_stage):
    ctx = dash.callback_context

    if not ctx.triggered:
        raise PreventUpdate

    # Get most recently triggered id and prop_type
    splitted = ctx.triggered[0]["prop_id"].split(".")
    prop_id = splitted[0]

    if prop_id == "value-adder-btn":
        line = build_value_setter_line(
            "value-setter-panel-{}".format(len(settings_children)),
            state_value[params[1]]["data"][cur_stage],
            daq.NumericInput(
                id={
                    'type': 'num-input',
                    'index': 'test-{}'.format(len(settings_children))
                }, value=0, className="setting-input", size=200, max=9999999
            ),
            len(settings_children)
        )
        settings_children.append(line)
    elif prop_id == "value-setter-view-btn" and len(settings_children) > 1:
        del settings_children[-1]
    return settings_children


@app.callback(
    [Output({'type': 'value-div', 'index': MATCH}, "children"),
     Output({'type': 'num-input', 'index': MATCH}, "value")],
    Input({'type': 'metric-select-dropdown', 'index': MATCH}, "value"),
    [State({'type': 'metric-select-dropdown', 'index': MATCH}, "id"),
     State("value-setter-store", "data"),
     State("n-interval-stage", "data"),
     State("owned-currencies", "data")]
)
def update_currency_price(value, _id, state_value, cur_stage, owned_currencies):
    amount = 0
    if value in owned_currencies:
        amount = owned_currencies[value]["amount"]
    return state_value[value]["data"][cur_stage], amount


# ===== Callbacks to update values based on store data and dropdown selection =====
# @app.callback(
#     output=[
#         Output("value-setter-panel", "children"),
#         Output("ud_usl_input", "value"),
#         Output("ud_lsl_input", "value"),
#         Output("ud_ucl_input", "value"),
#         Output("ud_lcl_input", "value"),
#     ],
#     inputs=[Input("metric-select-dropdown", "value")],
#     state=[State("value-setter-store", "data")],
# )
# def build_value_setter_panel(dd_select, state_value):
#     print("bla")
#     return (
#         [
#             build_value_setter_line(
#                 "value-setter-panel-header",
#                 "Specs",
#                 "Historical Value",
#                 "Set new value",
#             ),
#             build_value_setter_line(
#                 "value-setter-panel-usl",
#                 "Upper Specification limit",
#                 state_dict[dd_select]["usl"],
#                 ud_usl_input,
#             ),
#             build_value_setter_line(
#                 "value-setter-panel-lsl",
#                 "Lower Specification limit",
#                 state_dict[dd_select]["lsl"],
#                 ud_lsl_input,
#             ),
#             build_value_setter_line(
#                 "value-setter-panel-ucl",
#                 "Upper Control limit",
#                 state_dict[dd_select]["ucl"],
#                 ud_ucl_input,
#             ),
#             build_value_setter_line(
#                 "value-setter-panel-lcl",
#                 "Lower Control limit",
#                 state_dict[dd_select]["lcl"],
#                 ud_lcl_input,
#             ),
#         ],
#         state_value[dd_select]["usl"],
#         state_value[dd_select]["lsl"],
#         state_value[dd_select]["ucl"],
#         state_value[dd_select]["lcl"],
#     )


# ====== Callbacks to update stored data via click =====
@app.callback(
    output=[Output("owned-currencies", "data"),
            Output("initial-portfolio-value", "data"),
            Output("value-setter-view-output", "children")],
    inputs=[Input("value-setter-set-btn", "n_clicks")],
    state=[
        State({'type': 'metric-select-dropdown', 'index': ALL}, 'value'),
        State({'type': 'num-input', 'index': ALL}, "value"),
        State({'type': 'value-div', 'index': ALL}, "children"),
        State("owned-currencies", "data")
    ],
)
def set_value_setter_store(n_clicks, dd_select, num_input_select, values, owned_currencies):
    if n_clicks is None:
        raise PreventUpdate

    new_df_dict = {
        "Cryptocurrency": [],
        "Amount": [],
    }

    for i, currency in enumerate(dd_select):
        if num_input_select[i] > 0:
            owned_currencies[dd_select[i]] = {"amount": num_input_select[i], "price": values[i+1]}
            new_df_dict["Cryptocurrency"].append(dd_select[i])
            new_df_dict["Amount"].append(num_input_select[i])

    new_portfolio_value = 0
    for item in owned_currencies.values():
        new_portfolio_value += item["amount"]

    if len(owned_currencies) > 0:
        new_df = pd.DataFrame.from_dict(new_df_dict)
        table_title = html.H5("Current configuration:", style={"padding": "0px 2rem"})
        data_table = dash_table.DataTable(
            style_header={"fontWeight": "bold", "color": "inherit"},
            style_as_list_view=True,
            fill_width=True,
            # style_cell_conditional=[
            #     {"if": {"column_id": "Specs"}, "textAlign": "left"}
            # ],
            style_cell={
                "backgroundColor": "white",
                "fontFamily": "Open Sans",
                "padding": "0 2rem",
                "color": "inherit",
                "border": "none",
                "textAlign": "left"
            },
            css=[
                # {"selector": "tr:hover td", "rule": "color: #91dfd2 !important;"},
                {"selector": "td", "rule": "border: none !important;"},
                {
                    "selector": ".dash-cell.focused",
                    "rule": "background-color: #1e2130 !important;",
                },
                {"selector": "table", "rule": "--accent: #1e2130;"},
                {"selector": "tr", "rule": "background-color: transparent"},
            ],
            data=new_df.to_dict("records"),
            columns=[{"id": c, "name": c} for c in ["Cryptocurrency", "Amount"]],
        )
        new_div = html.Div(children=[table_title, data_table])

        return owned_currencies, new_portfolio_value, new_div
    return owned_currencies, new_portfolio_value, dash.no_update


# # ====== Callbacks to update stored data via click =====
# @app.callback(
#     output=Output("value-setter-store", "data"),
#     inputs=[Input("value-setter-set-btn", "n_clicks")],
#     state=[
#         State("metric-select-dropdown", "value"),
#         State("value-setter-store", "data"),
#         State("ud_usl_input", "value"),
#         State("ud_lsl_input", "value"),
#         State("ud_ucl_input", "value"),
#         State("ud_lcl_input", "value"),
#     ],
# )
# def set_value_setter_store(set_btn, param, data, usl, lsl, ucl, lcl):
#     print("bla")
#     if set_btn is None:
#         return data
#     else:
#         data[param]["usl"] = usl
#         data[param]["lsl"] = lsl
#         data[param]["ucl"] = ucl
#         data[param]["lcl"] = lcl
#
#         # Recalculate ooc in case of param updates
#         data[param]["ooc"] = populate_ooc(df[param], ucl, lcl)
#         return data


# @app.callback(
#     output=Output("value-setter-view-output", "children"),
#     inputs=[
#         Input("value-setter-view-btn", "n_clicks"),
#         Input("metric-select-dropdown", "value"),
#         Input("value-setter-store", "data"),
#     ],
# )
# def show_current_specs(n_clicks, dd_select, store_data):
#     print("bla")
#     if n_clicks > 0:
#         curr_col_data = store_data[dd_select]
#         new_df_dict = {
#             "Specs": [
#                 "Upper Specification Limit",
#                 "Lower Specification Limit",
#                 "Upper Control Limit",
#                 "Lower Control Limit",
#             ],
#             "Current Setup": [
#                 curr_col_data["usl"],
#                 curr_col_data["lsl"],
#                 curr_col_data["ucl"],
#                 curr_col_data["lcl"],
#             ],
#         }
#         new_df = pd.DataFrame.from_dict(new_df_dict)
#         return dash_table.DataTable(
#             style_header={"fontWeight": "bold", "color": "inherit"},
#             style_as_list_view=True,
#             fill_width=True,
#             style_cell_conditional=[
#                 {"if": {"column_id": "Specs"}, "textAlign": "left"}
#             ],
#             style_cell={
#                 "backgroundColor": "#1e2130",
#                 "fontFamily": "Open Sans",
#                 "padding": "0 2rem",
#                 "color": "darkgray",
#                 "border": "none",
#             },
#             css=[
#                 {"selector": "tr:hover td", "rule": "color: #91dfd2 !important;"},
#                 {"selector": "td", "rule": "border: none !important;"},
#                 {
#                     "selector": ".dash-cell.focused",
#                     "rule": "background-color: #1e2130 !important;",
#                 },
#                 {"selector": "table", "rule": "--accent: #1e2130;"},
#                 {"selector": "tr", "rule": "background-color: transparent"},
#             ],
#             data=new_df.to_dict("rows"),
#             columns=[{"id": c, "name": c} for c in ["Specs", "Current Setup"]],
#         )


# decorator for list of output
def create_callback(param):
    def callback(interval, stored_data):
        count, ooc_n = update_count(
            interval, param, stored_data
        )
        spark_line_data = update_sparkline(interval, param)
        return count, spark_line_data, ooc_n

    return callback


for param in params[1:]:
    update_param_row_function = create_callback(param)
    app.callback(
        output=[
            Output(param + suffix_count, "children"),
            Output(param + suffix_sparkline_graph, "extendData"),
            Output(param + suffix_ooc_n, "children"),
            # Output(param + suffix_ooc_g, "value"),
            # Output(param + suffix_indicator, "color"),
        ],
        inputs=[Input("interval-component", "n_intervals")],
        state=[State("value-setter-store", "data")],
    )(update_param_row_function)

@app.callback(
    output=[Output("portfolio-value", "data"),
            Output("portfolio-str", "children")],
    inputs=[
        Input("interval-component", "n_intervals"),
    ],
    state=[State("value-setter-store", "data"),
           State("owned-currencies", "data"),
           State("portfolio-value", "data"),
           State("interval-component", "disabled"),
           State("initial-portfolio-value", "data")]
)
def update_portfolio_value(interval, data, owned_currencies, portfolio_value, disabled, initial_portfolio_value):
    if disabled or not owned_currencies:
        return portfolio_value, "--"

    if len(portfolio_value) == 0:
        portfolio_value.append(initial_portfolio_value)

    new_portfolio_value = 0
    for item in owned_currencies:
        new_portfolio_value += (owned_currencies[item]["amount"] * data[item]["data"][interval]) / owned_currencies[item]["price"]

    portfolio_value.append(new_portfolio_value)

    return portfolio_value, str(round(new_portfolio_value, 2)) + "$"


#  ======= button to choose/update figure based on click ============
@app.callback(
    output=Output("control-chart-live", "figure"),
    inputs=[
        Input("interval-component", "n_intervals"),
        # Input(params[1] + suffix_button_id, "n_clicks"),
        # Input(params[2] + suffix_button_id, "n_clicks"),
        # Input(params[3] + suffix_button_id, "n_clicks"),
        # Input(params[4] + suffix_button_id, "n_clicks"),
        # Input(params[5] + suffix_button_id, "n_clicks"),
        # Input(params[6] + suffix_button_id, "n_clicks"),
        # Input(params[7] + suffix_button_id, "n_clicks"),
    ],
    state=[State("value-setter-store", "data"),
           # State("control-chart-live", "figure"),
           State("portfolio-value", "data"),
           State("initial-portfolio-value", "data")],
)
def update_control_chart(interval, data, portfolio_value, initial_portfolio_value):
    # Find which one has been triggered
    # ctx = dash.callback_context

    # if not ctx.triggered:
    return generate_graph(interval, data, portfolio_value, initial_portfolio_value)

    # if ctx.triggered:
    #     # Get most recently triggered id and prop_type
    #     splitted = ctx.triggered[0]["prop_id"].split(".")
    #     prop_id = splitted[0]
    #     prop_type = splitted[1]
    #
    #     if prop_type == "n_clicks":
    #         curr_id = cur_fig["data"][0]["name"]
    #         prop_id = prop_id[:-7]
    #         if curr_id == prop_id:
    #             return generate_graph(interval, data, curr_id)
    #         else:
    #             return generate_graph(interval, data, prop_id)
    #
    #     if prop_type == "n_intervals" and cur_fig is not None:
    #         curr_id = cur_fig["data"][0]["name"]
    #         return generate_graph(interval, data, curr_id)


# Update piechart
@app.callback(
    output=Output("piechart", "figure"),
    inputs=[# Input("interval-component", "n_intervals"),
            Input("dashboard-button", "n_clicks")],
    state=[State("value-setter-store", "data"),
           State("owned-currencies", "data"),
           State("initial-portfolio-value", "data")],
)
def update_piechart(interval, stored_data, owned_currencies, initial_portfolio_value):
    if interval == 0:
        return {
            "data": [],
            "layout": {
                "font": {"color": "white"},
                "paper_bgcolor": "rgba(0,0,0,0)",
                "plot_bgcolor": "rgba(0,0,0,0)",
            },
        }

    if interval >= max_length:
        total_count = max_length - 1
    else:
        total_count = interval - 1

    values = []
    colors = []
    for item in owned_currencies.values():
        # ooc_param = (stored_data[param]["ooc"][total_count] * 100) + 1
        values.append(item["amount"] / initial_portfolio_value)
        colors.append("#051C2C")
        # if ooc_param > 6:
        #     colors.append("#051C2C")
        # else:
        #     colors.append("#034B6F")

    new_figure = {
        "data": [
            {
                "labels": params[1:],
                "values": values,
                "type": "pie",
                "marker": {"colors": colors, "line": dict(color="white", width=2)},
                "hoverinfo": "percent",
                "textinfo": "label",
            }
        ],
        "layout": {
            "margin": dict(t=20, b=50),
            "uirevision": True,
            "font": {"color": "white"},
            "showlegend": False,
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "autosize": True,
        },
    }
    return new_figure


# Running the server
if __name__ == "__main__":
    app.run_server(host="0.0.0.0", debug=True, port=8050)
