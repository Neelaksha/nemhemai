import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict
import base64


def fig_to_base64(fig) -> str:
    """
    Convert Plotly figure to base64 PNG image
    """
    img_bytes = fig.to_image(format="png", engine="kaleido")
    return "data:image/png;base64," + base64.b64encode(img_bytes).decode("utf-8")


def save_fig_to_file(fig, filename: str) -> str:
    """
    Save Plotly figure to a file in the static directory.
    Returns the file path.
    """
    import os
    # Ensure static dir exists (though we created it, let's be safe)
    if not os.path.exists("static"):
        os.makedirs("static")
    
    path = os.path.join("static", filename)
    fig.write_image(path, engine="kaleido")
    return path


def create_revenue_chart_image(sales_data: List[Dict], return_fig: bool = False):
    """
    Line chart: revenue over time
    """
    if not sales_data:
        return None if return_fig else ""

    df_dict = {
        "period": [s["period"] for s in sales_data],
        "revenue": [s["revenue"] for s in sales_data],
    }

    fig = px.line(
        df_dict,
        x="period",
        y="revenue",
        title="Sales Revenue Over Time",
        labels={"revenue": "Revenue ($)", "period": "Period"},
    )

    fig.update_layout(
        showlegend=False,
        width=700,
        height=400
    )

    if return_fig:
        return fig

    return fig_to_base64(fig)


def create_metrics_chart_image(metrics: Dict, return_fig: bool = False):
    """
    Bar chart: key metrics dashboard
    """
    categories = ["Revenue", "Orders", "AOV"]
    values = [
        metrics["total_revenue"],
        metrics["total_orders"],
        metrics["avg_order_value"],
    ]

    fig = go.Figure(
        data=[
            go.Bar(
                x=categories,
                y=values,
                text=[f"{v:,.0f}" for v in values],
                textposition="auto",
            )
        ]
    )

    fig.update_layout(
        title="Key Metrics Dashboard",
        showlegend=False,
        width=600,
        height=350,
    )

    return fig_to_base64(fig)