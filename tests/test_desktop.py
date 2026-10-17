import base64
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from src.launcher.desktop_engine import DesktopEngine
from src.engine.manager import DeviceManager
from src.api.studio import StudioRack
from src.adapters.base import MidiPortInfo, PortDirection

class TestDesktopTransport(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.events = []
        self.engine = DesktopEngine(Path(self.tmp.name)/'config.json', self.events.append, use_virtual=True)
        self.engine.start()
    def tearDown(self):
        self.engine.close()
        self.assertFalse(self.engine.thread.is_alive())
        self.tmp.cleanup()
    def call(self,path,body=None):
        r=self.engine.submit('/api/'+path,'POST' if body is not None else 'GET',json.dumps(body) if body is not None else '').result(5)
        return r,json.loads(base64.b64decode(r['body']))
    def test_in_process_note_and_receiver_delivery(self):
        _,r=self.call('studio/connect/keyboard',{}); self.call('ports/input/select',{'port_name':r['keyboard_port']})
        for on in (True,False):self.call('studio/note',{'note':60,'on':on,'channel':1,'velocity':100})
        self.assertEqual(self.call('status')[1]['monitor']['rx_count'],2)
        self.assertEqual(len([e for e in self.events if e['type']=='midi_message']),2)
        _,r=self.call('studio/connect/pedal',{});self.call('ports/output/select',{'port_name':r['pedal_port']})
        self.call('send/control-change',{'channel':1,'controller':11,'value':96})
        self.assertEqual(self.call('studio/state')[1]['pedal']['cc']['11'],96)
    def test_invalid_messages_and_external_urls_rejected(self):
        r,_=self.call('studio/note',{'note':128,'on':True})
        self.assertEqual(r['status'],422)
        with self.assertRaises(ValueError):self.engine.submit('https://example.com/api/status').result(5)
    def test_mode_change_disconnects_and_releases(self):
        _,r=self.call('studio/connect/keyboard',{});self.call('ports/input/select',{'port_name':r['keyboard_port']})
        self.call('studio/note',{'note':60,'on':True})
        self.call('studio/mode',{'mode':'loopmidi'})
        status=self.call('status')[1]
        self.assertIsNone(status['selected_input'])
        self.assertEqual(self.call('studio/state')[1]['held_notes'],0)

class TestInputIsolation(unittest.TestCase):
    def test_hardware_selection_unsubscribes_internal_source(self):
        class Adapter:
            def get_input_ports(self):return [MidiPortInfo(id='hardware',name='Hardware',direction=PortDirection.INPUT)]
            def open_input(self,port,callback):return True
        with patch.object(DeviceManager,'start_hotplug_monitor',lambda self:None):
            mgr=DeviceManager(use_virtual=True);mgr.adapter=Adapter()
            rack=StudioRack(enabled=False,transport_mode='internal');mgr.set_internal_rack(rack)
            received=[]
            mgr.select_input(rack.keyboard_port_name,lambda *args:received.append(args))
            rack.connect('keyboard');mgr.select_input('Hardware',lambda *args:None)
            rack.note(60,1,100,True);rack.note(60,1,100,False)
            self.assertEqual(received,[])
            rack.close()
    def test_disconnected_receiver_does_not_claim_receipt(self):
        with patch.object(DeviceManager,'start_hotplug_monitor',lambda self:None):
            mgr=DeviceManager(use_virtual=True);rack=StudioRack(enabled=False,transport_mode='internal');mgr.set_internal_rack(rack)
            mgr.select_output(rack.pedal_port_name)
            self.assertFalse(mgr.send_to_selected_output(bytes([0xC0,24])))
            self.assertEqual(rack.pedal.snapshot()['received'],0)
