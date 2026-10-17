"""
FastAPI Server for PulseStage MIDI
Provides REST Endpoints, WebSocket Event Streaming, Dynamic Path Resolution, and Security Boundary Enforcement.
"""
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional, Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, PlainTextResponse

from ..core.profiles import ProfileRegistry
from ..core.codec import decode_message
from ..core.models import Direction
from ..engine.manager import DeviceManager
from ..engine.clock import MidiClock
from ..engine.monitor import MidiMonitor
from ..engine.actions import ActionRunner
from ..engine.config_store import ConfigStore
from .routes import init_routes
from .studio import StudioRack, studio_routes


def create_app(
    config_path: Optional[Path] = None,
    use_virtual: bool = False,
    event_sink=None,
) -> FastAPI:
    # Dynamic path resolution
    base_src_dir = Path(__file__).resolve().parent.parent
    project_root = base_src_dir.parent

    if not config_path:
        config_path = project_root / "config" / "user_config.json"

    # Shared application state
    app_state = {
        "main_loop": None,
        "active_websockets": set(),
    }

    # Thread-safe WebSocket broadcaster
    def broadcast_message(msg: dict):
        if event_sink:
            event_sink(msg)
        loop = app_state.get("main_loop")
        ws_set = app_state.get("active_websockets")
        if not loop or loop.is_closed() or not ws_set:
            return

        for ws in list(ws_set):
            try:
                asyncio.run_coroutine_threadsafe(_safe_send(ws, msg), loop)
            except Exception:
                pass

    async def _safe_send(ws: WebSocket, msg: dict):
        try:
            await ws.send_json(msg)
        except Exception:
            app_state["active_websockets"].discard(ws)

    def _on_port_disconnect(port_name: str):
        broadcast_message({"type": "port_disconnect", "message": f"Port '{port_name}' disconnected."})

    # Initialize Subsystems with disconnect notification
    config_store = ConfigStore(config_path)
    profile_registry = ProfileRegistry()
    manager = DeviceManager(use_virtual=use_virtual, disconnect_callback=_on_port_disconnect)
    monitor = MidiMonitor(capacity=1000)

    # Initialize studio rack with internal practice transport as default out-of-the-box
    studio_rack = StudioRack(enabled=not use_virtual, transport_mode='internal')
    manager.set_internal_rack(studio_rack)

    # Clock send callback: sends to hardware AND records outgoing clock/transport
    def _clock_send(data: bytes) -> bool:
        if not manager.selected_output_name:
            return False
        sent = manager.send_to_port(manager.selected_output_name, data)
        if sent:
            msg = decode_message(data, port_name=manager.selected_output_name, direction=Direction.TX)
            monitor.record_message(msg)
            # Broadcast transport changes, throttle raw clock ticks over WS
            if msg.message_type.value in ("START", "STOP", "CONTINUE"):
                broadcast_message({"type": "clock_status", "state": msg.message_type.value, "bpm": clock.bpm})
        return sent

    def _clock_error(err: str):
        broadcast_message({"type": "port_disconnect", "message": err})

    clock = MidiClock(send_callback=_clock_send, error_callback=_clock_error)
    saved_bpm = config_store.get_preference("clock_bpm", 120.0)
    clock.set_bpm(saved_bpm)

    # Action runner send callback with full broadcast
    def _action_send(port_name: str, data: bytes) -> bool:
        return manager.send_to_port(port_name, data)

    def _action_monitor_cb(msg):
        monitor.record_message(msg)
        broadcast_message({"type": "midi_message", "message": msg.model_dump()})

    action_runner = ActionRunner(send_func=_action_send, monitor_callback=_action_monitor_cb)

    # Restore preferences
    preferred_out = config_store.get_preference("selected_output_name")
    if preferred_out and manager.is_port_connected(preferred_out):
        manager.select_output(preferred_out)

    preferred_in = config_store.get_preference("selected_input_name")
    if preferred_in and manager.is_port_connected(preferred_in):
        def _in_cb(port_id: str, data: bytes, ts: float):
            decoded = decode_message(data, timestamp_ms=ts, port_name=preferred_in, direction=Direction.RX)
            monitor.record_message(decoded)
            broadcast_message({"type": "midi_message", "message": decoded.model_dump()})
        manager.select_input(preferred_in, _in_cb)

    # Lifespan: captures event loop and ensures clean shutdown
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app_state["main_loop"] = asyncio.get_running_loop()
        yield
        # Shutdown cleanup
        clock.emergency_stop()
        action_runner.cancel()
        studio_rack.close()
        manager.stop_hotplug_monitor()
        manager.adapter.close_all()

    app = FastAPI(title="PulseStage MIDI", version="1.1.0", lifespan=lifespan)

    # Local Origin Security Middleware
    @app.middleware("http")
    async def security_boundary_middleware(request, call_next):
        origin = request.headers.get("origin")
        if origin:
            allowed = [
                "http://localhost", "http://127.0.0.1",
                "https://localhost", "https://127.0.0.1",
                "app://pulse-stage"
            ]
            if not any(origin.startswith(a) for a in allowed):
                return PlainTextResponse("Forbidden: Untrusted Origin", status_code=403)
        return await call_next(request)

    # Restrict CORS to localhost and local application origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:8765",
            "http://127.0.0.1:8765",
            "http://localhost:8788",
            "http://127.0.0.1:8788",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "app://pulse-stage",
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # Mount REST Routes
    routes = init_routes(
        manager=manager,
        clock=clock,
        monitor=monitor,
        action_runner=action_runner,
        config_store=config_store,
        profile_registry=profile_registry,
        broadcast_func=broadcast_message,
    )
    app.include_router(routes)
    def changing_studio_mode():
        clock.emergency_stop()
        action_runner.cancel()
        manager.deselect_input()
        manager.deselect_output()
    app.include_router(studio_routes(studio_rack, changing_studio_mode))

    # WebSocket Endpoint with Origin Security Verification
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        origin = websocket.headers.get("origin")
        if origin:
            allowed = [
                "http://localhost", "http://127.0.0.1",
                "https://localhost", "https://127.0.0.1",
                "app://pulse-stage"
            ]
            if not any(origin.startswith(a) for a in allowed):
                await websocket.close(code=1008, reason="Forbidden: Untrusted WebSocket Origin")
                return

        await websocket.accept()
        app_state["active_websockets"].add(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                # Handle client ping
                if data == "ping":
                    await websocket.send_text("pong")
        except WebSocketDisconnect:
            app_state["active_websockets"].discard(websocket)
        except Exception:
            app_state["active_websockets"].discard(websocket)

    # Static UI Mount using dynamic path
    ui_dir = base_src_dir / "ui"
    if ui_dir.exists():
        app.mount("/static", StaticFiles(directory=str(ui_dir)), name="static")

        @app.get("/")
        async def serve_index():
            return FileResponse(str(ui_dir / "index.html"))

    return app
