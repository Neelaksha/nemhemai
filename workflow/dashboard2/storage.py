import json
import os

FILE = "storage.json"

def load_charts():
    if not os.path.exists(FILE):
        return []
    with open(FILE, "r") as f:
        return json.load(f)

def save_chart(chart):
    data = load_charts()
    data.append(chart)
    with open(FILE, "w") as f:
        json.dump(data, f, indent=2)