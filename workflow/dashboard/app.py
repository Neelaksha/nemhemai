import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import numpy as np

# Create some mock data
np.random.seed(42)
dates = pd.date_range(start='2023-01-01', periods=100)
df = pd.DataFrame({
    'Date': dates,
    'Revenue': np.random.normal(1000, 100, 100).cumsum(),
    'Users': np.random.normal(500, 50, 100).cumsum(),
    'Category': np.random.choice(['Electronics', 'Clothing', 'Food', 'Books'], 100)
})

category_df = df.groupby('Category')['Revenue'].sum().reset_index()

# Initialize the Dash app with a Bootstrap theme
# We use dbc.themes.FLATLY for a clean, modern look similar to Superset
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY, dbc.icons.FONT_AWESOME])

# --- Components ---

# 1. Navbar
navbar = dbc.NavbarSimple(
    brand="Data Analytics Dashboard",
    brand_href="#",
    color="primary",
    dark=True,
    fluid=True,
    className="mb-4 shadow-sm"
)

# 2. KPI Cards
def create_kpi_card(title, value, icon_class, color):
    return dbc.Card(
        dbc.CardBody([
            html.Div([
                html.I(className=f"{icon_class} fa-2x", style={"color": color}),
                html.Div([
                    html.H5(title, className="card-title text-muted mb-0", style={"fontSize": "0.9rem", "fontWeight": "600"}),
                    html.H3(value, className="card-text fw-bold mb-0")
                ], className="ms-3")
            ], className="d-flex align-items-center")
        ]),
        className="shadow-sm border-0 mb-4 h-100",
        style={"borderRadius": "10px"}
    )

kpi_row = dbc.Row([
    dbc.Col(create_kpi_card("Total Revenue", "$1.2M", "fas fa-dollar-sign", "#28a745"), md=3, sm=6, xs=12),
    dbc.Col(create_kpi_card("Active Users", "45,231", "fas fa-users", "#17a2b8"), md=3, sm=6, xs=12),
    dbc.Col(create_kpi_card("New Signups", "1,203", "fas fa-user-plus", "#ffc107"), md=3, sm=6, xs=12),
    dbc.Col(create_kpi_card("Conversion Rate", "4.5%", "fas fa-chart-line", "#dc3545"), md=3, sm=6, xs=12),
])

# 3. Charts
# Line Chart: Revenue over Time
fig_line = px.line(df, x='Date', y='Revenue', title="Revenue Trend")
fig_line.update_layout(
    margin=dict(l=20, r=20, t=50, b=20),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    title_font=dict(size=18, family="Inter, sans-serif", color="#333"),
    font=dict(family="Inter, sans-serif"),
    hovermode="x unified"
)
fig_line.update_traces(line=dict(width=3, color="#007bff"))

# Bar Chart: Revenue by Category
fig_bar = px.bar(category_df, x='Category', y='Revenue', title="Revenue by Category", color='Category', 
                 color_discrete_sequence=px.colors.qualitative.Pastel)
fig_bar.update_layout(
    margin=dict(l=20, r=20, t=50, b=20),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    showlegend=False,
    title_font=dict(size=18, family="Inter, sans-serif", color="#333"),
    font=dict(family="Inter, sans-serif")
)

# Pie Chart
fig_pie = px.pie(category_df, names='Category', values='Revenue', title="Market Share", hole=0.4,
                 color_discrete_sequence=px.colors.qualitative.Pastel)
fig_pie.update_layout(
    margin=dict(l=20, r=20, t=50, b=20),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    title_font=dict(size=18, family="Inter, sans-serif", color="#333"),
    font=dict(family="Inter, sans-serif"),
    legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
)

def create_chart_card(figure):
    return dbc.Card(
        dbc.CardBody([dcc.Graph(figure=figure, config={'displayModeBar': False})]),
        className="shadow-sm border-0 mb-4",
        style={"borderRadius": "10px"}
    )

charts_row_1 = dbc.Row([
    dbc.Col(create_chart_card(fig_line), md=8),
    dbc.Col(create_chart_card(fig_pie), md=4),
])

charts_row_2 = dbc.Row([
    dbc.Col(create_chart_card(fig_bar), md=12)
])

# --- App Layout ---
app.layout = html.Div([
    navbar,
    dbc.Container([
        kpi_row,
        charts_row_1,
        charts_row_2
    ], fluid=True, className="px-4", style={"minHeight": "100vh", "paddingTop": "10px", "backgroundColor": "#f8f9fa"})
])

if __name__ == '__main__':
    # Changed from run_server() to run() to fix dash 2.x ObsoleteAttributeException
    app.run(debug=True, port=8050)
