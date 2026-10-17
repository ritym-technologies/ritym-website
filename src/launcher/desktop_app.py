"""
PulseStage MIDI - Dedicated Desktop Application Launcher
Manages single-instance lifecycle, user AppData isolation, background Uvicorn engine,
and dedicated frameless desktop window.
"""
import argparse
import ctypes
import json
import os
import socket
import subprocess
import sys
import threading
import time
from typing import Optional
import urllib.request
import webbrowser
from pathlib import Path

# Resolve root whether running from source or PyInstaller frozen bundle
if getattr(sys, 'frozen', False):
    APP_ROOT = Path(sys._MEIPASS)
    IS_FROZEN = True
else:
    APP_ROOT = Path(__file__).resolve().parent.parent.parent
    IS_FROZEN = False

if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

import uvicorn
from src.api.server import create_app


def get_user_data_dir() -> Path:
    """Returns the writable per-user AppData directory for PulseStage."""
    app_data = os.environ.get("APPDATA")
    if app_data:
        base = Path(app_data) / "PulseStage"
    else:
        base = Path.home() / ".pulsestage"
    base.mkdir(parents=True, exist_ok=True)
    (base / "config").mkdir(parents=True, exist_ok=True)
    (base / "logs").mkdir(parents=True, exist_ok=True)
    (base / "exports").mkdir(parents=True, exist_ok=True)
    return base


def ensure_user_config(user_data_dir: Path) -> Path:
    """Ensures a valid user_config.json exists in user AppData."""
    config_file = user_data_dir / "config" / "user_config.json"
    if not config_file.exists():
        # Default configuration
        default_config = {
            "schema_version": 1,
            "preferences": {
                "theme": "dark",
                "clock_bpm": 120.0,
                "selected_output_name": None,
                "selected_input_name": None,
                "preset_convention": "ZERO_INDEXED"
            },
            "actions": []
        }
        try:
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not create default user config: {e}")
    return config_file


def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(('127.0.0.1', port)) == 0


def check_existing_instance(port: int = 8765) -> bool:
    """Checks if another PulseStage instance is already responding on loopback."""
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{port}/api/status", headers={"User-Agent": "PulseStage-Launcher"})
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode('utf-8'))
                if "PulseStage" in data.get("application", "") or "PulseStage" in data.get("app_name", ""):
                    return True
    except Exception:
        pass
    return False


def launch_dedicated_window(url: str) -> Optional[subprocess.Popen]:
    """
    Launches a dedicated standalone desktop application window using Edge or Chrome app mode.
    Edge is built into Windows 10/11 and provides an isolated, frameless window experience.
    """
    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]

    candidates = edge_paths + chrome_paths
    for path in candidates:
        if os.path.exists(path):
            try:
                proc = subprocess.Popen([
                    path,
                    f"--app={url}",
                    "--window-size=1380,940",
                    "--window-position=60,60"
                ])
                return proc
            except Exception:
                pass

    # Fallback to standard system browser
    webbrowser.open(url)
    return None


def main():
    parser = argparse.ArgumentParser(description="PulseStage MIDI Studio - Standalone Desktop Station")
    parser.add_argument("--port", type=int, default=8765, help="Port to bind (default: 8765)")
    parser.add_argument("--virtual", action="store_true", help="Force virtual simulation adapter")
    parser.add_argument("--headless", action="store_true", help="Run server without opening UI window")
    args = parser.parse_args()

    # Single-instance check
    if check_existing_instance(args.port):
        print(f"PulseStage is already running on http://127.0.0.1:{args.port}.")
        launch_dedicated_window(f"http://127.0.0.1:{args.port}")
        sys.exit(0)

    # Resolve port conflicts if another program occupies 8765
    port = args.port
    if is_port_in_use(port) and not check_existing_instance(port):
        # Find next free port
        for candidate in range(8766, 8800):
            if not is_port_in_use(candidate):
                port = candidate
                break

    user_data = get_user_data_dir()
    config_path = ensure_user_config(user_data)
    app = create_app(config_path=config_path, use_virtual=args.virtual)
    url = f"http://127.0.0.1:{port}"

    server_config = uvicorn.Config(
        app=app,
        host="127.0.0.1",
        port=port,
        log_level="warning",
        loop="asyncio"
    )
    server = uvicorn.Server(server_config)

    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()

    # Wait for server to accept requests
    for _ in range(50):
        time.sleep(0.1)
        if is_port_in_use(port):
            break

    window_proc = None
    if not args.headless:
        window_proc = launch_dedicated_window(url)

    if window_proc:
        # Keep launcher alive while window is open
        try:
            window_proc.wait()
        except KeyboardInterrupt:
            pass
        # Window was closed by user -> cleanly stop server
        server.should_exit = True
        server_thread.join(timeout=2.0)
    else:
        # Browser fallback or headless -> wait for server thread
        try:
            while server_thread.is_alive():
                time.sleep(0.5)
        except KeyboardInterrupt:
            server.should_exit = True
            server_thread.join(timeout=2.0)


if __name__ == "__main__":
    main()
