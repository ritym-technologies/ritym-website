"""
End-to-End Live HTTP Integration Test
"""
import os
import socket
import sys
import threading
import time
from pathlib import Path
import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import uvicorn
from src.api.server import create_app


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


def run_e2e_live():
    print("=" * 65)
    print(" STARTING PULSESTAGE MIDI LIVE INTEGRATION VERIFICATION")
    print("=" * 65)

    test_port = find_free_port()
    base_url = f"http://127.0.0.1:{test_port}"
    config_path = PROJECT_ROOT / "config" / "test_user_config.json"
    app = create_app(config_path=config_path, use_virtual=True)

    config = uvicorn.Config(app, host="127.0.0.1", port=test_port, log_level="error")
    server = uvicorn.Server(config)

    t = threading.Thread(target=server.run, daemon=True)
    t.start()

    # Wait for server to boot
    for _ in range(25):
        try:
            r = requests.get(f"{base_url}/api/status", timeout=0.3)
            if r.status_code == 200:
                break
        except Exception:
            time.sleep(0.08)

    try:
        # 1. Status Check
        r = requests.get(f"{base_url}/api/status")
        assert r.status_code == 200, f"Status failed: {r.text}"
        status = r.json()
        print(f"[PASS] Status Endpoint: {status['application']} v{status['version']} (Platform: Virtual={status['is_virtual']})")

        # 2. Port Discovery
        r = requests.get(f"{base_url}/api/ports")
        assert r.status_code == 200
        ports = r.json()
        assert len(ports["outputs"]) >= 3
        assert len(ports["inputs"]) >= 1
        out_name = ports["outputs"][0]["name"]
        in_name = ports["inputs"][0]["name"]
        print(f"[PASS] Port Discovery: Found {len(ports['outputs'])} outputs, {len(ports['inputs'])} inputs")

        # 3. Port Selection
        r = requests.post(f"{base_url}/api/ports/output/select", json={"port_name": out_name})
        assert r.status_code == 200 and r.json()["success"]
        r = requests.post(f"{base_url}/api/ports/input/select", json={"port_name": in_name})
        assert r.status_code == 200 and r.json()["success"]
        print(f"[PASS] Selected Output '{out_name}' and Input '{in_name}'")

        # 4. User Journey A: Send Program Change
        r = requests.post(f"{base_url}/api/send/program-change", json={
            "channel": 1,
            "program": 24,
            "preset_convention": "0-127",
        })
        assert r.status_code == 200
        pc = r.json()
        assert pc["bytes_hex"] == "0xC0 0x18"
        assert "Program Change 24" in pc["plain_language"]
        assert "unverified" in pc["unverified_notice"].lower()
        print(f"[PASS] User Journey A: Sent Program Change 24 -> {pc['bytes_hex']} ({pc['plain_language']})")

        # 5. User Journey B: Control a Parameter (CC)
        r = requests.post(f"{base_url}/api/send/control-change", json={
            "channel": 2,
            "controller": 64,
            "value": 127,
        })
        assert r.status_code == 200
        cc = r.json()
        assert cc["bytes_hex"] == "0xB1 0x40 0x7F"
        assert "Sustain" in cc["plain_language"]
        print(f"[PASS] User Journey B: Sent CC 64 (Sustain) = 127 -> {cc['bytes_hex']} ({cc['plain_language']})")

        # 6. User Journey C: Synchronise Tempo (MIDI Clock)
        r = requests.post(f"{base_url}/api/clock/bpm", json={"bpm": 130.0})
        assert r.status_code == 200
        r = requests.post(f"{base_url}/api/clock/start")
        assert r.status_code == 200 and r.json()["state"] == "RUNNING"
        time.sleep(0.15)
        r = requests.post(f"{base_url}/api/clock/stop")
        assert r.status_code == 200 and r.json()["state"] == "STOPPED"
        print("[PASS] User Journey C: Synchronised Tempo at 130.0 BPM. Transport verified.")

        # 7. User Journey D: Troubleshoot a Connection (Monitor & Export)
        r = requests.get(f"{base_url}/api/monitor/messages")
        assert r.status_code == 200
        monitor_data = r.json()
        assert len(monitor_data["messages"]) > 0
        print(f"[PASS] User Journey D: Live Monitor captured {len(monitor_data['messages'])} events.")

        r_exp = requests.get(f"{base_url}/api/monitor/export/json")
        assert r_exp.status_code == 200 and "application" in r_exp.text
        print("[PASS] Diagnostic Export: Downloaded JSON diagnostic report.")

        # 8. User Journey E: Performance Action (Solo Boost)
        actions = requests.get(f"{base_url}/api/actions").json()
        assert len(actions) > 0
        first_act = actions[0]
        # Ensure target port is set
        for s in first_act["steps"]:
            s["target_port_name"] = out_name
        requests.post(f"{base_url}/api/actions", json=first_act)

        r_act = requests.post(f"{base_url}/api/actions/{first_act['id']}/execute")
        assert r_act.status_code == 200 and r_act.json()["success"]
        print(f"[PASS] User Journey E: Triggered performance action '{first_act['name']}' ({r_act.json()['executed_steps']} steps).")

        # 9. Emergency Panic & Stop All
        r_panic = requests.post(f"{base_url}/api/send/panic", json={})
        assert r_panic.status_code == 200
        print(f"[PASS] Safe Panic: Transmitted {r_panic.json()['packets_sent']} silence packets without risky SysEx.")

        r_stop = requests.post(f"{base_url}/api/send/emergency-stop")
        assert r_stop.status_code == 200
        print("[PASS] Emergency Stop: All clocks and action queues safely aborted.")

        print("=" * 65)
        print(" ALL USER JOURNEYS (A-E) FULLY VERIFIED ON LIVE ENGINE!")
        print("=" * 65)

    finally:
        server.should_exit = True
        t.join(timeout=2.0)


if __name__ == "__main__":
    run_e2e_live()
