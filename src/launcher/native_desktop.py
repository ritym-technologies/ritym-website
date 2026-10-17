"""Bundled desktop renderer and native IPC. No browser executable or HTTP listener."""
import argparse, base64, hashlib, json, logging, mimetypes, os, sys
from pathlib import Path

APP_ROOT = Path(sys._MEIPASS) if getattr(sys, 'frozen', False) else Path(__file__).resolve().parents[2]
if str(APP_ROOT) not in sys.path: sys.path.insert(0, str(APP_ROOT))
from src.launcher.desktop_engine import DesktopEngine

def get_user_data_dir(override=None):
    root = Path(override) if override else Path(os.environ.get('APPDATA', Path.home())) / 'PulseStage'
    for folder in ('config', 'logs', 'exports', 'renderer'): (root / folder).mkdir(parents=True, exist_ok=True)
    return root

def ensure_user_config(root):
    config = root / 'config/user_config.json'
    if not config.exists():
        from src.engine.config_store import ConfigStore
        store = ConfigStore(config); store._data['actions'] = []; store.save()
    return config

def self_check(report):
    import tempfile
    with tempfile.TemporaryDirectory(prefix='PulseStage-check-') as folder:
        engine = DesktopEngine(ensure_user_config(get_user_data_dir(folder)), use_virtual=True); engine.start()
        def call(path, body=None):
            r = engine.submit('/api/' + path, 'POST' if body is not None else 'GET', json.dumps(body) if body is not None else '').result(10)
            if r['status'] != 200: raise RuntimeError(str(r))
            return json.loads(base64.b64decode(r['body']))
        try:
            rack = call('studio/connect/keyboard', {}); call('ports/input/select', {'port_name': rack['keyboard_port']})
            for on in (True, False): call('studio/note', {'note':60, 'channel':1, 'velocity':100, 'on':on})
            rack = call('studio/connect/pedal', {}); call('ports/output/select', {'port_name':rack['pedal_port']})
            call('send/program-change', {'channel':1, 'program':24})
            assert call('status')['monitor']['rx_count'] == 2
            assert call('studio/state')['pedal']['program'] == 24
            result = {'passed':True, 'transport':'in-process IPC', 'network_listener':False, 'external_browser_required':False, 'keyboard_rx':2, 'received_program':24}
        finally: engine.close()
        if report: Path(report).write_text(json.dumps(result, indent=2), encoding='utf-8')
        elif sys.stdout: print(json.dumps(result, indent=2))
    return 0

def main():
    parser = argparse.ArgumentParser(description='PulseStage desktop MIDI studio')
    parser.add_argument('--data-dir', help=argparse.SUPPRESS)
    parser.add_argument('--self-check', action='store_true', help='Check the internal engine without hardware')
    parser.add_argument('--report', help='Save self-check JSON')
    parser.add_argument('--verify-desktop', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.self_check: return self_check(args.report)
    if args.verify_desktop and (not args.data_dir or not args.report):
        parser.error('Desktop verification requires isolated --data-dir and --report paths.')
    from PySide6.QtCore import QByteArray, QBuffer, QFile, QIODevice, QObject, QUrl, Signal, Slot, QTimer, Qt, QSettings, QLockFile
    from PySide6.QtGui import QIcon, QAction
    from PySide6.QtNetwork import QLocalServer, QLocalSocket
    from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QFileDialog, QDialog, QVBoxLayout
    from PySide6.QtWebChannel import QWebChannel
    from PySide6.QtWebEngineCore import QWebEngineUrlScheme, QWebEngineUrlSchemeHandler, QWebEngineUrlRequestJob, QWebEnginePage, QWebEngineProfile, QWebEngineScript, QWebEngineUrlRequestInterceptor
    from PySide6.QtWebEngineWidgets import QWebEngineView
    scheme = QWebEngineUrlScheme(b'pulsestage'); scheme.setSyntax(QWebEngineUrlScheme.Syntax.Host)
    scheme.setFlags(QWebEngineUrlScheme.Flag.SecureScheme | QWebEngineUrlScheme.Flag.CorsEnabled)
    QWebEngineUrlScheme.registerScheme(scheme)
    QApplication.setApplicationName('PulseStage'); QApplication.setOrganizationName('PulseStage'); QApplication.setApplicationVersion('1.1.0')
    app = QApplication(sys.argv[:1]); root = get_user_data_dir(args.data_dir)
    log = open(root / 'logs/desktop.log', 'a', encoding='utf-8', buffering=1)
    if sys.stdout is None: sys.stdout = log
    if sys.stderr is None: sys.stderr = log
    logging.basicConfig(filename=root/'logs/desktop.log', level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s', force=True)
    app.setWindowIcon(QIcon(str(APP_ROOT/'pulsestage.ico')))
    # User-scoped Windows named pipe. It never opens a TCP/IP port.
    name = 'PulseStage-' + hashlib.sha256(str(root.resolve()).lower().encode()).hexdigest()[:20]
    # Windows permits multiple named-pipe servers with the same name. An owned
    # process lock, not listen() alone, elects the single primary MIDI engine.
    process_lock = QLockFile(str(root/'desktop.lock')); process_lock.setStaleLockTime(0)
    if not process_lock.tryLock(0):
        existing = QLocalSocket(); existing.connectToServer(name)
        if existing.waitForConnected(1500):
            existing.write(b'activate'); existing.waitForBytesWritten(1000); existing.disconnectFromServer(); return 0
        QMessageBox.critical(None, 'PulseStage', 'Another instance is starting or the desktop connection is unavailable. Try again shortly.'); return 1
    instance = QLocalServer(app); instance.setSocketOptions(QLocalServer.SocketOption.UserAccessOption)
    if not instance.listen(name):
        process_lock.unlock(); QMessageBox.critical(None,'PulseStage','The local desktop connection could not start.'); return 1

    class Bridge(QObject):
        reply = Signal(str, str)
        midiEvent = Signal(str)
        export_ready = Signal(str, bytes)
        checkFinished = Signal(str)
        responseReady = Signal(str, str)
        midiReady = Signal(str)
        def __init__(self):
            super().__init__(); self.engine = None; self.pending = set()
            self.responseReady.connect(self.deliver, Qt.ConnectionType.QueuedConnection)
            self.midiReady.connect(self.publish, Qt.ConnectionType.QueuedConnection)
        @Slot(str, str)
        def deliver(self, identifier, value):
            self.pending.discard(identifier)
            if args.verify_desktop: logging.info('Desktop reply on GUI thread: %s', identifier)
            self.reply.emit(identifier, value)
        @Slot(str)
        def publish(self, value):
            self.midiEvent.emit(value)
        @Slot(str, str)
        def request(self, identifier, payload):
            if self.engine.closed: return
            def respond(value): self.responseReady.emit(identifier, json.dumps(value))
            try:
                if len(self.pending) >= 128 or identifier in self.pending: raise RuntimeError('Too many pending requests')
                value = json.loads(payload)
                if args.verify_desktop: logging.info('Desktop API: %s', value['path'])
                future = self.engine.submit(value['path'], value.get('method','GET'), value.get('body',''))
                self.pending.add(identifier)
                def completed(task):
                    try: respond(task.result())
                    except Exception:
                        logging.exception('Desktop request failed')
                        respond({'status':500, 'headers':{'content-type':'application/json'}, 'body':base64.b64encode(b'{"detail":"Desktop request failed. See diagnostics."}').decode()})
                future.add_done_callback(completed)
            except Exception:
                logging.exception('Invalid desktop request')
                respond({'status':400, 'headers':{'content-type':'application/json'}, 'body':base64.b64encode(b'{"detail":"Invalid desktop request."}').decode()})
        @Slot(str)
        def saveTheme(self, theme):
            if theme in ('dark','light'): QSettings().setValue('theme',theme)
        @Slot(str)
        def saveExport(self, path):
            if path not in ('/api/monitor/export/json','/api/monitor/export/csv','/api/monitor/export/text','/api/config/export'): return
            def completed(task):
                try:
                    r = task.result()
                    if r['status']==200: self.export_ready.emit(path, base64.b64decode(r['body']))
                except Exception: logging.exception('Export failed')
            self.engine.submit(path).add_done_callback(completed)
        @Slot(str)
        def finishCheck(self, result):
            if args.verify_desktop:
                self.checkFinished.emit(result)

    class Assets(QWebEngineUrlSchemeHandler):
        def requestStarted(self, job):
            url = job.requestUrl()
            if url.host()!='studio' or job.requestMethod()!=b'GET': job.fail(QWebEngineUrlRequestJob.Error.RequestDenied); return
            if url.path()=='/guide': allowed=APP_ROOT/'docs'; path=allowed/'PULSESTAGE-USER-GUIDE.html'
            else:
                allowed=APP_ROOT/'src/ui'
                path=allowed/('index.html' if url.path()=='/' else url.path().removeprefix('/static/').lstrip('/'))
            path=path.resolve()
            if not path.is_relative_to(allowed.resolve()) or not path.is_file(): job.fail(QWebEngineUrlRequestJob.Error.UrlNotFound); return
            content = path.read_bytes()
            buffer=QBuffer(job); buffer.setData(QByteArray(content)); buffer.open(QIODevice.OpenModeFlag.ReadOnly)
            mime={'.js':'application/javascript','.css':'text/css','.html':'text/html'}.get(path.suffix,mimetypes.guess_type(path.name)[0] or 'application/octet-stream')
            job.reply(mime.encode(),buffer)

    class LocalRequests(QWebEngineUrlRequestInterceptor):
        def interceptRequest(self, info):
            url=info.requestUrl()
            if not ((url.scheme()=='pulsestage' and url.host()=='studio') or url.scheme() in ('qrc','data','blob')): info.block(True)
    class LocalPage(QWebEnginePage):
        def acceptNavigationRequest(self,url,nav_type,main_frame): return url.scheme()=='pulsestage' and url.host()=='studio'
        def javaScriptConsoleMessage(self,level,message,line,source): logging.info('UI %s:%s %s',source,line,message)

    bridge=Bridge(); engine=DesktopEngine(ensure_user_config(root),event_sink=lambda value:bridge.midiReady.emit(json.dumps(value))); bridge.engine=engine
    try: engine.start()
    except Exception as error:
        logging.exception('Startup failed'); QMessageBox.critical(None,'PulseStage could not start',str(error)); instance.close(); return 1
    class Window(QMainWindow):
        def closeEvent(self,event):
            self.setEnabled(False)
            try: engine.close()
            except Exception as error:
                logging.exception('Shutdown failed'); QMessageBox.warning(self,'PulseStage shutdown',str(error))
            instance.close(); process_lock.unlock(); event.accept()
    window=Window(); window.setWindowTitle('PulseStage — MIDI Studio'); window.resize(1380,940); window.setMinimumSize(900,650)
    profile=QWebEngineProfile('PulseStage',window); profile.setPersistentStoragePath(str(root/'renderer/storage')); profile.setCachePath(str(root/'renderer/cache'))
    assets=Assets(profile); profile.installUrlSchemeHandler(b'pulsestage',assets)
    interceptor=LocalRequests(profile); profile.setUrlRequestInterceptor(interceptor)
    page=LocalPage(profile,window); channel=QWebChannel(page); channel.setPropertyUpdateInterval(0); channel.registerObject('pulseStage',bridge); page.setWebChannel(channel)
    resource=QFile(':/qtwebchannel/qwebchannel.js')
    if not resource.open(QIODevice.OpenModeFlag.ReadOnly): raise RuntimeError('Bundled desktop channel library is missing')
    script=QWebEngineScript(); script.setName('PulseStage native transport')
    script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation); script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld); script.setRunsOnSubFrames(False)
    script.setSourceCode('window.PulseStageTheme='+json.dumps(QSettings().value('theme','dark'))+';\n'+bytes(resource.readAll()).decode('utf-8')+'\n'+(APP_ROOT/'src/ui/js/desktop-transport.js').read_text(encoding='utf-8')); page.scripts().insert(script)
    view=QWebEngineView(window); view.setPage(page); window.setCentralWidget(view); page.load(QUrl('pulsestage://studio/'))
    check_result = {'passed': False}
    if args.verify_desktop:
        def finish_check(raw):
            check_result.update(json.loads(raw))
            Path(args.report).write_text(json.dumps(check_result, indent=2), encoding='utf-8')
            window.close()
        bridge.checkFinished.connect(finish_check)
        def check_loaded(ok):
            logging.info('Desktop QA interface loaded: %s', ok)
            if ok:
                page.runJavaScript((APP_ROOT/'src/ui/js/desktop-smoke.js').read_text(encoding='utf-8'))
            else:
                finish_check(json.dumps({'passed':False,'error':'The bundled interface failed to load.'}))
        page.loadFinished.connect(check_loaded)
        QTimer.singleShot(30000, lambda: finish_check(json.dumps({'passed':False,'error':'The renderer check timed out.'})))
    @Slot(str,bytes)
    def save_export(path,contents):
        ext='json' if path.endswith('/export') else path.rsplit('/',1)[-1]
        if ext=='text': ext='txt'
        filename,_=QFileDialog.getSaveFileName(window,'Save PulseStage capture',str(root/'exports'/('PulseStage-capture.'+ext)))
        if filename:
            try: Path(filename).write_bytes(contents)
            except OSError as error: QMessageBox.warning(window,'Export failed',str(error))
    bridge.export_ready.connect(save_export)
    def activate():
        while instance.hasPendingConnections():
            client=instance.nextPendingConnection(); client.close(); client.deleteLater()
        window.showNormal(); window.raise_(); window.activateWindow()
    instance.newConnection.connect(activate)
    help_action=QAction('User guide',window)
    def show_guide():
        dialog=QDialog(window); dialog.setWindowTitle('PulseStage user guide'); dialog.resize(1000,800)
        layout=QVBoxLayout(dialog); guide=QWebEngineView(dialog); guide.setPage(LocalPage(profile,guide)); guide.load(QUrl('pulsestage://studio/guide')); layout.addWidget(guide); dialog.exec()
    help_action.triggered.connect(show_guide); window.menuBar().addMenu('Help').addAction(help_action)
    window.show(); result=app.exec(); engine.close()
    import shiboken6
    view.setPage(QWebEnginePage(view)); shiboken6.delete(page); shiboken6.delete(window)
    return (0 if check_result['passed'] else 1) if args.verify_desktop else result

if __name__=='__main__': raise SystemExit(main())
