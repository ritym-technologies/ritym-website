"""Run the existing application routes inside the desktop process, without sockets."""
import asyncio
import base64
import concurrent.futures
import json
import threading
from urllib.parse import urlsplit
from src.api.server import create_app


class DesktopEngine:
    def __init__(self, config_path, event_sink=None, use_virtual=False):
        self.config_path = config_path
        self.event_sink = event_sink
        self.use_virtual = use_virtual
        self.loop = None
        self.app = None
        self.error = None
        self.closed = False
        self.ready = threading.Event()
        self.thread = threading.Thread(target=self._run, name='PulseStage MIDI engine')

    def start(self):
        self.thread.start()
        if not self.ready.wait(15):
            raise RuntimeError('The MIDI engine did not start in time.')
        if self.error:
            raise RuntimeError(f'The MIDI engine could not start: {self.error}') from self.error

    def _run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        async def lifetime():
            try:
                self.app = create_app(config_path=self.config_path, use_virtual=self.use_virtual,
                                      event_sink=self.event_sink)
                async with self.app.router.lifespan_context(self.app):
                    self.stopping = asyncio.Event()
                    self.ready.set()
                    await self.stopping.wait()
            except Exception as error:
                self.error = error
                self.ready.set()
                raise
        try:
            self.loop.run_until_complete(lifetime())
        except Exception:
            import logging
            logging.exception('Desktop engine failed')
        finally:
            pending = asyncio.all_tasks(self.loop)
            for task in pending:
                task.cancel()
            if pending:
                self.loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            self.loop.run_until_complete(self.loop.shutdown_asyncgens())
            self.loop.close()

    async def dispatch(self, path, method='GET', body=''):
        url = urlsplit(path)
        if url.scheme or url.netloc or not url.path.startswith('/api/'):
            raise ValueError('Only local application API requests are permitted.')
        if method not in ('GET', 'POST', 'PUT', 'PATCH', 'DELETE'):
            raise ValueError('Unsupported application request method.')
        payload = body.encode('utf-8')
        if len(payload) > 1024 * 1024:
            raise ValueError('Application request is too large.')
        messages = []
        delivered = False
        finished = asyncio.Event()
        async def receive():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {'type': 'http.request', 'body': payload, 'more_body': False}
            await finished.wait()
            return {'type': 'http.disconnect'}
        async def send(message):
            messages.append(message)
            if message['type'] == 'http.response.body' and not message.get('more_body', False):
                finished.set()
        scope = {'type': 'http', 'asgi': {'version': '3.0', 'spec_version': '2.4'},
                 'http_version': '1.1', 'method': method, 'scheme': 'pulsestage',
                 'path': url.path, 'raw_path': url.path.encode(), 'root_path': '',
                 'query_string': url.query.encode(), 'headers': [(b'content-type', b'application/json')],
                 'server': None, 'client': None}
        await self.app(scope, receive, send)
        start = next(m for m in messages if m['type'] == 'http.response.start')
        content = b''.join(m.get('body', b'') for m in messages if m['type'] == 'http.response.body')
        headers = {k.decode('latin1'): v.decode('latin1') for k, v in start['headers']}
        return {'status': start['status'], 'headers': headers,
                'body': base64.b64encode(content).decode('ascii')}

    def submit(self, path, method='GET', body=''):
        if not self.loop or not self.thread.is_alive() or self.error:
            raise RuntimeError('The MIDI engine is unavailable.')
        return asyncio.run_coroutine_threadsafe(self.dispatch(path, method, body), self.loop)

    def close(self):
        self.closed = True
        if self.loop and self.thread.is_alive():
            self.loop.call_soon_threadsafe(self.stopping.set)
            self.thread.join(timeout=10)
            if self.thread.is_alive():
                raise RuntimeError('The MIDI engine did not finish shutting down.')
