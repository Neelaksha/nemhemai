import sys
import os
import subprocess
import time
from llm_query import generate_dashboard_component
from storage import save_chart

def main():
    # 1. Get the prompt from command line or input
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
    else:
        prompt = input("Enter your natural language prompt for the dashboard: ")

    if not prompt.strip():
        print("Error: Empty prompt. Please provide a description of the data you want to see.")
        return

    print(f"\n--- 🤖 Processing Prompt: '{prompt}' ---")
    
    # 2. Generate the dashboard component (SQL + Chart Type)
    try:
        result = generate_dashboard_component(prompt)
        print(f"✅ Generated SQL: {result['query']}")
        print(f"📊 Recommended Chart: {result['chart_type']}")
        
        # 3. Save to storage.json
        save_chart(result)
        print("📁 Saved to dashboard storage!")
        
    except Exception as e:
        print(f"❌ Error during generation: {e}")
        return

    # 4. Automatically start the dashboard app
    print("\n--- 🚀 Starting Dash Dashboard ---")
    print("Dashboard will be available at http://127.0.0.1:8050")
    
    try:
        # We use subprocess.run so the user can see the logs
        subprocess.run(["python", "app.py"])
    except KeyboardInterrupt:
        print("\nDashboard stopped.")

if __name__ == "__main__":
    main()
