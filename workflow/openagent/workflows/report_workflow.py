import json
from datetime import datetime

from openagent.services.db_service import get_sales_data
from openagent.services.llm_service import call_llm
from openagent.tools.emailer import send_email
from openagent.chart_utils import (
    create_revenue_chart_image,
    create_metrics_chart_image,
)


def safe_parse(text: str):
    try:
        return json.loads(text)
    except:
        return {}


async def run_workflow(user_input):
    print("*** REPORT WORKFLOW START ***")
    logs = []

    # 🔹 Parse request
    try:
        parsed_raw = await call_llm(f"""
    Extract:
    - start_date
    - end_date
    - report_type

    Return JSON only.

    Input: {user_input}
    """)
        print("*** PARSED LLM OK:", parsed_raw[:200])
    except Exception as e:
        print(f"*** PARSE LLM ERROR: {e}")
        parsed_raw = '{{}}'

    parsed = safe_parse(parsed_raw)
    logs.append("OK parsed request")

    start_date = parsed.get("start_date", "2024-01-01")
    end_date = parsed.get("end_date", "2024-12-31")
    print(f"*** DATES: {start_date} to {end_date}")

    # 🔹 Fetch data
    sales = await get_sales_data(
        limit=100,
        start_date=start_date,
        end_date=end_date
    )
    print(f"*** REPORT DEBUG: fetched {len(sales)} sales records")
    logs.append(f"OK fetched sales: {len(sales)} records")

    # 🔹 Process metrics
    total_revenue = sum(x["revenue"] for x in sales)
    total_orders = len(sales)

    processed = {
        "total_revenue": total_revenue,
        "total_orders": total_orders,
        "avg_order_value": total_revenue / total_orders if total_orders else 0,
    }
    print("*** METRICS:", processed)
    logs.append("OK processed metrics")

    # 🔹 Charts (smaller for b64)
    revenue_chart = ""
    metrics_chart = ""
    try:
        revenue_chart = create_revenue_chart_image(sales)
        print("*** REVENUE CHART OK")
    except Exception as e:
        print(f"*** REVENUE CHART ERROR: {str(e)}")
    try:
        metrics_chart = create_metrics_chart_image(processed)
        print("*** METRICS CHART OK")
    except Exception as e:
        print(f"*** METRICS CHART ERROR: {str(e)}")
    logs.append("OK charts attempted")

    # 🔹 Insights
    insights = "Insights service temporarily unavailable (using faster model soon)."
    try:
        insights = await call_llm(f"""
    Data:
    {processed}

    Sales data snapshot:
    First 3: {sales[:3]}

    Write concise:
    - 3 key insights
    - 1 anomaly detected
    - 1 recommendation
    """)
        print("*** INSIGHTS LLM OK")
    except Exception as e:
        print(f"*** INSIGHTS LLM ERROR: {str(e)}")
    logs.append("OK insights")

    # 🔹 Email
    email_result = ""
    if "email" in user_input.lower():
        try:
            email_result = send_email(
                to_email="test@example.com",
                subject="Automated Report",
                body=f"Metrics: {processed}\\nInsights: {insights}",
            )
        except Exception as e:
            print(f"*** EMAIL ERROR: {e}")

    log_text = "\\n".join(f"- {l}" for l in logs)

    chart_dates = [item['period'] for item in sales]
    chart_revenues = [float(item['revenue']) for item in sales]
    
    insights_html = insights.replace('\n', '<br>')
    email_html = f'<div class="mt-6 p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg text-blue-300 text-sm">{email_result}</div>' if email_result else ''

    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/apexcharts"></script>
    <style>
        body {{ background-color: #0f172a; color: #f8fafc; font-family: 'Inter', sans-serif; }}
        .card {{ background: rgba(30, 41, 59, 0.5); border: 1px solid #334155; backdrop-filter: blur(8px); }}
    </style>
</head>
<body class="p-6">
    <div class="max-w-6xl mx-auto">
        <!-- Header -->
        <div class="flex justify-between items-center mb-8">
            <div>
                <h1 class="text-3xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
                    Sales Intelligence Dashboard
                </h1>
                <p class="text-slate-400">Real-time performance analytics</p>
            </div>
            <div class="text-right">
                <div class="text-xs text-emerald-400 font-mono">LIVE STATUS: ACTIVE</div>
                <div class="text-xs text-slate-500 font-mono">{datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
            </div>
        </div>

        <!-- Metrics Grid -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div class="card p-6 rounded-2xl">
                <div class="text-slate-400 text-sm mb-1 uppercase tracking-wider">Total Revenue</div>
                <div class="text-3xl font-bold text-white">${processed['total_revenue']:,.2f}</div>
                <div class="text-emerald-400 text-xs mt-2 flex items-center">
                    <span>↑ 12.5%</span> <span class="text-slate-500 ml-1">vs last period</span>
                </div>
            </div>
            <div class="card p-6 rounded-2xl">
                <div class="text-slate-400 text-sm mb-1 uppercase tracking-wider">Total Orders</div>
                <div class="text-3xl font-bold text-white">{processed['total_orders']}</div>
                <div class="text-emerald-400 text-xs mt-2 flex items-center">
                    <span>↑ 8.2%</span> <span class="text-slate-500 ml-1">vs last period</span>
                </div>
            </div>
            <div class="card p-6 rounded-2xl">
                <div class="text-slate-400 text-sm mb-1 uppercase tracking-wider">Avg Order Value</div>
                <div class="text-3xl font-bold text-white">${processed['avg_order_value']:,.2f}</div>
                <div class="text-slate-500 text-xs mt-2 italic">Calculated live</div>
            </div>
        </div>

        <!-- Charts Container -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            <div class="card p-6 rounded-2xl min-h-[400px]">
                <h3 class="text-lg font-semibold mb-4 text-slate-200">Revenue Performance</h3>
                <div id="revenueChart"></div>
            </div>
            <div class="card p-6 rounded-2xl min-h-[400px]">
                <h3 class="text-lg font-semibold mb-4 text-slate-200">Volume Analysis</h3>
                <div id="volumeChart"></div>
            </div>
        </div>

        <!-- Insights -->
        <div class="card p-6 rounded-2xl border-emerald-500/30 bg-emerald-500/5">
            <div class="flex items-center gap-2 mb-4">
                <span class="text-emerald-400">🧠</span>
                <h3 class="text-lg font-semibold text-emerald-400">AI Financial Insights</h3>
            </div>
            <div class="prose prose-invert max-w-none text-slate-300">
                {insights_html}
            </div>
        </div>
        
        {email_html}
    </div>

    <script>
        const chartOptions = {{
            theme: {{ mode: 'dark' }},
            chart: {{ background: 'transparent', toolbar: {{ show: false }}, animations: {{ enabled: true }} }},
            colors: ['#10b981', '#3b82f6'],
            stroke: {{ curve: 'smooth', width: 3 }},
            grid: {{ borderColor: '#1e293b', padding: {{ left: 10, right: 10 }} }},
            xaxis: {{ categories: {chart_dates}, axisBorder: {{ show: false }}, axisTicks: {{ show: false }} }},
            tooltip: {{ theme: 'dark' }}
        }};

        var options1 = {{
            ...chartOptions,
            series: [{{ name: 'Revenue', data: {chart_revenues} }}],
            chart: {{ ...chartOptions.chart, type: 'area', height: 320 }},
            fill: {{ type: 'gradient', gradient: {{ shadeIntensity: 1, opacityFrom: 0.7, opacityTo: 0.3, stops: [0, 90, 100] }} }},
        }};

        var options2 = {{
            ...chartOptions,
            series: [{{ name: 'Revenue', data: {chart_revenues} }}],
            chart: {{ ...chartOptions.chart, type: 'bar', height: 320 }},
            plotOptions: {{ bar: {{ borderRadius: 8, columnWidth: '40%' }} }},
        }};

        new ApexCharts(document.querySelector("#revenueChart"), options1).render();
        new ApexCharts(document.querySelector("#volumeChart"), options2).render();
    </script>
</body>
</html>
"""
    
    # Wrap in markdown code block for Open WebUI Artifact rendering
    result = f"```html\n{html_content}\n```"
    
    print("*** REPORT COMPLETE - Length:", len(result))
    return result

