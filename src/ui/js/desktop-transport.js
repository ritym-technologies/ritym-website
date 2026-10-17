/* Injected only in PulseStage's embedded window. No HTTP or WebSocket listener. */
(() => {
  if (location.protocol !== 'pulsestage:') return;
  let channel;
  let nextId = 0;
  const pending = new Map();
  const ready = new Promise((resolve, reject) => {
    const timeout = setTimeout(() => reject(Error('The desktop connection did not start. Restart PulseStage.')), 15000);
    new QWebChannel(qt.webChannelTransport, c => {
      channel = c.objects.pulseStage;
      channel.reply.connect((id, value) => {
        const request = pending.get(String(id));
        if (!request) return;
        clearTimeout(request.timer); pending.delete(String(id));
        const response = JSON.parse(value);
        const bytes = Uint8Array.from(atob(response.body || ''), c => c.charCodeAt(0));
        // IPC already supplies a complete body. Avoid Chromium's streamed Response
        // task queue for this custom scheme; it can stall while the window is idle.
        const text = new TextDecoder().decode(bytes);
        request.resolve({status: response.status, ok: response.status >= 200 && response.status < 300,
          headers: new Headers(response.headers), json: async () => JSON.parse(text),
          text: async () => text, arrayBuffer: async () => bytes.buffer,
          blob: async () => new Blob([bytes])});
      });
      clearTimeout(timeout); resolve(channel);
    });
  });
  window.PulseStageDesktop = {ready};
  window.fetch = async (input, options = {}) => {
    const bridge = await ready;
    const url = new URL(typeof input === 'string' ? input : input.url, location.href);
    if (url.protocol !== 'pulsestage:' || url.host !== 'studio' || !url.pathname.startsWith('/api/'))
      throw Error('Only local PulseStage requests are allowed.');
    const id = String(++nextId);
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {pending.delete(id); reject(Error('The desktop request timed out.'));}, 30000);
      pending.set(id, {resolve, reject, timer});
      bridge.request(id, JSON.stringify({path: url.pathname + url.search,
        method: options.method || 'GET', body: options.body || ''}));
    });
  };
  window.open = path => { ready.then(b => b.saveExport(String(path))); return null; };
  navigator.sendBeacon = (path, data) => {
    const body = data instanceof Blob ? data.text() : Promise.resolve(String(data || ''));
    body.then(body => fetch(path, {method: 'POST', body})).catch(() => {});
    return true;
  };
})();
