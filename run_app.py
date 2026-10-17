"""
PulseStage MIDI - Desktop Application Launcher
Starts the high-performance core engine and opens the stage-ready UI in standalone app mode.
"""
import argparse
import os
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import uvicorn
from src.api.server import create_app


def launch_browser_app(url: str):
    """
    Launches Chrome or Edge in standalone frameless app mode (--app=URL)
    for a native desktop application experience.
    """
    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]

    for p in edge_paths + chrome_paths:
        if os.path.exists(p):
            try:
                subprocess.Popen([p, f"--app={url}"])
                return
            except Exception:
                pass

    # Fallback to standard system browser
    webbrowser.open(url)


def main():
    parser = argparse.ArgumentParser(description="PulseStage MIDI - Stage Control & Diagnostics Station")
    parser.add_argument("--host", default="127.0.0.1", help="Binding host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8765, help="Port number (default: 8765)")
    parser.add_argument("--virtual", action="store_true", help="Force virtual MIDI simulation adapter")
    parser.add_argument("--no-browser", action="store_true", help="Run in headless mode without opening UI window")
    args = parser.parse_args()

    config_path = PROJECT_ROOT / "config" / "user_config.json"
    app = create_app(config_path=config_path, use_virtual=args.virtual)

    url = f"http://{args.host}:{args.port}"
    print("=" * 65)
    print(" PULSESTAGE MIDI - STAGE CONTROL & DIAGNOSTICS STATION")
    print(f" Web Interface:  {url}")
    print(f" Platform Mode:  {'Virtual (Simulation)' if args.virtual or sys.platform != 'win32' else 'Native Windows WinMM'}")
    print(" Touring Ready:  Drift-Compensated 24 PPQN Clock + Safe Panic")
    print("=" * 65)

    if not args.no_browser:
        import threading
        def _open():
            time.sleep(1.2)
            launch_browser_app(url)
        threading.Thread(target=_open, daemon=True).start()

    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
