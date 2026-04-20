# tools.py

def get_sales_data():
    return {
        "revenue": 12000,
        "growth": "8%",
        "period": "last week"
    }


def summarize_sales(data):
    return f"""
Sales Report ({data['period']}):
- Revenue: ${data['revenue']}
- Growth: {data['growth']}
"""


def send_email(content):
    print("Sending email...")
    return f"✅ Email sent:\n{content}"