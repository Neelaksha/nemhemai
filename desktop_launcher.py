"""
NemhemAI - Desktop Application Launcher
Runs the FastAPI backend and opens it in a native desktop window
"""
import sys
import os
import threading
import time
import webview
import uvicorn
from multiprocessing import Process

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Set working directory to user data folder for persistence
if sys.platform == 'darwin':
    user_data_dir = os.path.expanduser('~/Library/Application Support/NemhemAI')
elif sys.platform == 'win32':
    user_data_dir = os.path.join(os.environ['APPDATA'], 'NemhemAI')
else:
    user_data_dir = os.path.expanduser('~/.nemhemai')

if not os.path.exists(user_data_dir):
    try:
        os.makedirs(user_data_dir)
    except OSError:
        pass # Fallback to temp or current dir if fails

try:
    os.chdir(user_data_dir)
    print(f"📂 Working directory set to: {user_data_dir}")
except OSError:
    print(f"⚠️ Failed to set working directory to {user_data_dir}")


def run_backend():
    """Run the FastAPI backend server"""
    # Set environment variable to prevent browser auto-open
    os.environ["DESKTOP_MODE"] = "1"
    
    from backend.main import app
    import uvicorn
    
    # Run without auto-browser opening
    port = int(os.getenv("PORT", 8000))
    print(f"🚀 Starting backend server on port {port}")
    
    # Run with minimal output
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=port,
        log_level="warning",
        access_log=False
    )

def wait_for_server(url="http://127.0.0.1:8000", timeout=30):
    """Wait for the backend server to be ready"""
    import requests
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{url}/health", timeout=1)
            if response.status_code == 200:
                print("✅ Backend server is ready!")
                return True
        except:
            pass
        time.sleep(0.5)
    
    return False

def main():
    """Main entry point for the desktop application"""
    print("=" * 50)
    print("     NemhemAI - Desktop Application")
    print("=" * 50)
    print()
    
    # Start backend server in a separate thread
    backend_thread = threading.Thread(target=run_backend, daemon=True)
    backend_thread.start()
    
    print("⏳ Waiting for backend to start...")
    
    # Wait for server to be ready
    if not wait_for_server():
        print("❌ Failed to start backend server!")
        return
    
    # Create and start the desktop window
    print("🪟 Opening application window...")
    
    window = webview.create_window(
        title='NemhemAI - AI Chat Assistant',
        url='http://127.0.0.1:8000',
        width=1400,
        height=900,
        resizable=True,
        fullscreen=False,
        min_size=(1024, 768),
        background_color='#FFFFFF',
        text_select=True
    )
    
    # Start the webview (this blocks until window is closed)
    webview.start(debug=False)
    
    print("\n👋 Application closed. Goodbye!")

if __name__ == "__main__":
    main()
