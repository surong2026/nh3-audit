"""
手动启动 Streamlit (用于 PythonAnywhere Console 或 Always-on task)
  cd nh3_audit && python start_streamlit.py
"""
import subprocess
import sys
import os

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

subprocess.run([
    sys.executable, "-m", "streamlit", "run", f"{PROJECT_DIR}/app.py",
    "--server.port", "8505",
    "--server.headless", "true",
    "--server.enableCORS", "false",
    "--server.enableXsrfProtection", "false",
    "--browser.gatherUsageStats", "false",
    "--server.fileWatcherType", "none",
], cwd=PROJECT_DIR)
