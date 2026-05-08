import dash
from dash import dcc, html, Input, Output, State
import plotly.express as px
from db import run_query
from storage import load_charts, save_chart

app = dash.Dash(__name__)
app.title = "Superset Clone (Dash + Postgres)"

# -------- Layout --------
app.layout = html.Div([
    html.H2("📊 Superset Clone"),

    dcc.Tabs(id="tabs", value="dashboard-tab", children=[
        # ---------- Dashboard ----------
        dcc.Tab(label="Dashboard", value="dashboard-tab", children=[
            html.Div(id="dashboard-container"),
            dcc.Interval(
                id='interval-component',
                interval=2*1000, # in milliseconds (2 seconds)
                n_intervals=0
            )
        ]),

        # ---------- SQL Editor ----------
        dcc.Tab(label="SQL Editor", value="sql-tab", children=[
            dcc.Textarea(
                id="sql-input",
                placeholder="SELECT * FROM sales_data",
                style={"width": "100%", "height": 150}
            ),

            dcc.Dropdown(
                id="chart-type",
                options=[
                    {"label": "Line", "value": "line"},
                    {"label": "Bar", "value": "bar"},
                    {"label": "Pie", "value": "pie"}
                ],
                value="line"
            ),

            html.Button("Run Query", id="run-btn"),
            html.Button("Save Chart", id="save-btn"),

            dcc.Graph(id="query-result"),
            html.Div(id="error-output", style={"color": "red"})
        ]),

        # ---------- Dashboard ----------
        ])
    ])
])

# -------- Run Query --------
@app.callback(
    Output("query-result", "figure"),
    Output("error-output", "children"),
    Input("run-btn", "n_clicks"),
    State("sql-input", "value"),
    State("chart-type", "value")
)
def run_sql(n, query, chart_type):
    if not n or not query:
        return {}, ""

    df, error = run_query(query)

    if error:
        return {}, error

    if df.empty:
        return {}, "No data returned"

    x = df.columns[0]
    y = df.columns[1] if len(df.columns) > 1 else None

    if chart_type == "line":
        fig = px.line(df, x=x, y=y)
    elif chart_type == "bar":
        fig = px.bar(df, x=x, y=y)
    else:
        fig = px.pie(df, names=x, values=y)

    return fig, ""

# -------- Save Chart --------
@app.callback(
    Output("save-btn", "children"),
    Input("save-btn", "n_clicks"),
    State("sql-input", "value"),
    State("chart-type", "value"),
    prevent_initial_call=True
)
def save_chart_callback(n, query, chart_type):
    if not query:
        return "No query"

    save_chart({
        "query": query,
        "chart_type": chart_type
    })

    return "Saved!"

# -------- Load Dashboard --------
@app.callback(
    Output("dashboard-container", "children"),
    Input("interval-component", "n_intervals")
)
def load_dashboard(n):
    charts = load_charts()
    components = []

    for chart in charts:
        df, error = run_query(chart["query"])
        if error or df is None or df.empty:
            continue

        x = df.columns[0]
        y = df.columns[1] if len(df.columns) > 1 else None

        if chart["chart_type"] == "line":
            fig = px.line(df, x=x, y=y)
        elif chart["chart_type"] == "bar":
            fig = px.bar(df, x=x, y=y)
        else:
            fig = px.pie(df, names=x, values=y)

        components.append(dcc.Graph(figure=fig))

    return html.Div(
        components,
        style={
            "display": "grid",
            "gridTemplateColumns": "1fr 1fr",
            "gap": "20px"
        }
    )

# -------- Run --------
if __name__ == "__main__":
    app.run(debug=True)