from flask import Flask, render_template_string
import webbrowser
import threading
import time
import json

app = Flask(__name__)

DASHBOARD_DATA = {
    "usage": [
        {"date": "2024-01-01", "users": 120, "documents": 45, "queries": 89},
        {"date": "2024-01-02", "users": 150, "documents": 60, "queries": 120},
        {"date": "2024-01-03", "users": 180, "documents": 75, "queries": 150},
        {"date": "2024-01-04", "users": 200, "documents": 90, "queries": 180},
    ],
    "document_types": [
        {"name": "Circulars", "value": 45},
        {"name": "SOPs", "value": 30},
        {"name": "Tenders", "value": 25},
    ],
    "top_queries": [
        {"query": "contract review", "count": 45},
        {"query": "compliance check", "count": 32},
        {"query": "tender analysis", "count": 28},
    ]
}

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

    <style>
        body {
            font-family: Arial;
            background: #f5f5f5;
            margin: 0;
            padding: 20px;
        }

        h1 { text-align: center; }

        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }

        .card {
            background: white;
            padding: 20px;
            border-radius: 10px;
        }
    </style>
</head>
<body>

<h1>📊 Dashboard</h1>

<div class="grid">
    <div class="card">
        <h3>Users Trend</h3>
        <canvas id="lineChart"></canvas>
    </div>

    <div class="card">
        <h3>Document Types</h3>
        <canvas id="pieChart"></canvas>
    </div>

    <div class="card">
        <h3>Top Queries</h3>
        <canvas id="barChart"></canvas>
    </div>
</div>

<script>
const data = {{ data | safe }};

// LINE CHART
new Chart(document.getElementById("lineChart"), {
    type: "line",
    data: {
        labels: data.usage.map(d => d.date),
        datasets: [{
            label: "Users",
            data: data.usage.map(d => d.users)
        }]
    }
});

// PIE CHART
new Chart(document.getElementById("pieChart"), {
    type: "pie",
    data: {
        labels: data.document_types.map(d => d.name),
        datasets: [{
            data: data.document_types.map(d => d.value)
        }]
    }
});

// BAR CHART
new Chart(document.getElementById("barChart"), {
    type: "bar",
    data: {
        labels: data.top_queries.map(d => d.query),
        datasets: [{
            label: "Count",
            data: data.top_queries.map(d => d.count)
        }]
    }
});
</script>

</body>
</html>
"""

@app.route("/")
def dashboard():
    return render_template_string(
        HTML,
        data=json.dumps(DASHBOARD_DATA)
    )

def open_browser():
    time.sleep(1)
    webbrowser.open("http://127.0.0.1:5001")

if __name__ == "__main__":
    threading.Thread(target=open_browser).start()
    app.run(port=5001, debug=False)