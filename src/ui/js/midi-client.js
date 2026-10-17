/**
 * PulseStage MIDI - WebSocket and REST API Client Bridge
 * Enforces res.ok checks and structured error propagation.
 */
class MidiClient {
  constructor(baseUrl = "") {
    this.baseUrl = baseUrl;
    this.ws = null;
    this.listeners = {
      message: [],
      clock: [],
      status: [],
      ports: [],
      port_disconnect: [],
    };
    this.isConnected = false;
  }

  initWebSocket() {
    const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    const wsUrl = `${proto}//${host}/ws`;

    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      this.isConnected = true;
      this._emit("status", { connected: true });
    };

    this.ws.onclose = () => {
      this.isConnected = false;
      this._emit("status", { connected: false });
      setTimeout(() => this.initWebSocket(), 2000);
    };

    this.ws.onerror = (err) => {
      console.warn("WebSocket error:", err);
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "midi_message") {
          this._emit("message", data.message);
        } else if (data.type === "clock_status") {
          this._emit("clock", data);
        } else if (data.type === "monitor_clear") {
          this._emit("monitor_clear", {});
        } else if (data.type === "port_disconnect") {
          this._emit("port_disconnect", data);
        }
      } catch (e) {
        console.error("Error parsing WS message:", e);
      }
    };
  }

  on(event, callback) {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(callback);
  }

  _emit(event, payload) {
    if (this.listeners[event]) {
      this.listeners[event].forEach(cb => cb(payload));
    }
  }

  async _request(url, options = {}) {
    const res = await fetch(url, options);
    if (!res.ok) {
      let msg = `HTTP ${res.status}: ${res.statusText}`;
      try {
        const body = await res.json();
        if (body.detail) {
          msg = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
        }
      } catch (e) {
        try {
          const txt = await res.text();
          if (txt) msg = txt;
        } catch (e2) {}
      }
      throw new Error(msg);
    }
    return await res.json();
  }

  async getStatus() {
    return await this._request(`${this.baseUrl}/api/status`);
  }

  async getPorts() {
    return await this._request(`${this.baseUrl}/api/ports`);
  }

  async selectOutput(portName) {
    return await this._request(`${this.baseUrl}/api/ports/output/select`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ port_name: portName }),
    });
  }

  async selectInput(portName) {
    return await this._request(`${this.baseUrl}/api/ports/input/select`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ port_name: portName }),
    });
  }

  async sendProgramChange(channel, program, presetConvention = "0-127") {
    return await this._request(`${this.baseUrl}/api/send/program-change`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        channel: parseInt(channel, 10),
        program: parseInt(program, 10),
        preset_convention: presetConvention,
      }),
    });
  }

  async sendControlChange(channel, controller, value) {
    return await this._request(`${this.baseUrl}/api/send/control-change`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        channel: parseInt(channel, 10),
        controller: parseInt(controller, 10),
        value: parseInt(value, 10),
      }),
    });
  }

  async sendBankSelect(channel, msb, lsb, program) {
    return await this._request(`${this.baseUrl}/api/send/bank-select`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        channel: parseInt(channel, 10),
        msb: parseInt(msb, 10),
        lsb: parseInt(lsb, 10),
        program: parseInt(program, 10),
      }),
    });
  }

  async panic() {
    return await this._request(`${this.baseUrl}/api/send/panic`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    });
  }

  async emergencyStop() {
    return await this._request(`${this.baseUrl}/api/send/emergency-stop`, {
      method: "POST",
    });
  }

  async startClock() {
    return await this._request(`${this.baseUrl}/api/clock/start`, { method: "POST" });
  }

  async stopClock() {
    return await this._request(`${this.baseUrl}/api/clock/stop`, { method: "POST" });
  }

  async continueClock() {
    return await this._request(`${this.baseUrl}/api/clock/continue`, { method: "POST" });
  }

  async setBpm(bpm) {
    return await this._request(`${this.baseUrl}/api/clock/bpm`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ bpm: parseFloat(bpm) }),
    });
  }

  async tapTempo() {
    return await this._request(`${this.baseUrl}/api/clock/tap`, { method: "POST" });
  }

  async getMonitorMessages(showRawClock = false) {
    return await this._request(`${this.baseUrl}/api/monitor/messages?show_raw_clock=${showRawClock}`);
  }

  async clearMonitor() {
    return await this._request(`${this.baseUrl}/api/monitor/clear`, { method: "POST" });
  }

  async toggleMonitorPause() {
    return await this._request(`${this.baseUrl}/api/monitor/pause`, { method: "POST" });
  }

  async getActions() {
    return await this._request(`${this.baseUrl}/api/actions`);
  }

  async saveAction(action) {
    return await this._request(`${this.baseUrl}/api/actions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(action),
    });
  }

  async deleteAction(actionId) {
    return await this._request(`${this.baseUrl}/api/actions/${actionId}`, {
      method: "DELETE",
    });
  }

  async executeAction(actionId) {
    return await this._request(`${this.baseUrl}/api/actions/${actionId}/execute`, {
      method: "POST",
    });
  }
  async sendPitchBend(channel, value) {
    return await this._request(`${this.baseUrl}/api/send/pitch-bend`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        channel: parseInt(channel, 10),
        value: parseInt(value, 10),
      }),
    });
  }

  async sendChannelPressure(channel, pressure) {
    return await this._request(`${this.baseUrl}/api/send/channel-pressure`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        channel: parseInt(channel, 10),
        pressure: parseInt(pressure, 10),
      }),
    });
  }

  async sendRawHex(hexString) {
    return await this._request(`${this.baseUrl}/api/send/raw-hex`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        hex_string: hexString,
      }),
    });
  }
}