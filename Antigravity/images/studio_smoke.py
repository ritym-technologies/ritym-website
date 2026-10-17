"""Native loopback smoke test against the isolated preview, never hardware ports."""
import json
import time
from pathlib import Path
import requests

BASE = 'http://127.0.0.1:18795/api/'
results = {'physical_hardware_tested': False, 'tests': {}}


def get(path):
    r = requests.get(BASE + path, timeout=4)
    r.raise_for_status()
    return r.json()


def post(path, data=None):
    r = requests.post(BASE + path, json=data or {}, timeout=4)
    r.raise_for_status()
    return r.json()


def select_output(name):
    # loopMIDI was restarted during port setup; discard any cached old handle.
    # Select, deselect and explicitly reopen without sending to a stale handle.
    post('ports/output/select', {'port_name': name})
    post('ports/output/select', {'port_name': None})
    post('ports/output/select', {'port_name': name})


try:
    post('studio/connect/pedal')
    select_output('PulseStage Pedal Test')
    post('send/program-change', {'channel': 2, 'program': 24})
    post('send/bank-select', {'channel': 2, 'msb': 1, 'lsb': 2, 'program': 9})
    post('send/control-change', {'channel': 2, 'controller': 11, 'value': 96})
    time.sleep(.15)
    pedal = get('studio/state')['pedal']
    packets = [event['bytes'] for event in pedal['events']]
    assert packets[-5:] == [[193, 24], [177, 0, 1], [177, 32, 2], [193, 9], [177, 11, 96]], packets
    results['tests']['program_bank_cc'] = {'passed': True, 'received': packets[-5:]}
    # Prove the receiver does not follow a Send response aimed at another port.
    before = pedal['sequence']
    select_output('PulseStage Keyboard')
    post('send/program-change', {'channel': 2, 'program': 55})
    time.sleep(.15)
    wrong = get('studio/state')['pedal']
    assert wrong['sequence'] == before and wrong['program'] == 9
    results['tests']['wrong_destination_no_false_confirmation'] = {'passed': True}
    select_output('PulseStage Pedal Test')
    post('clock/bpm', {'bpm': 120})
    post('clock/start')
    time.sleep(2.25)
    clock = get('studio/state')['pedal']
    post('clock/stop')
    assert clock['ticks'] >= 90 and clock['measured_bpm'] and abs(clock['measured_bpm'] - 120) < 3, clock
    results['tests']['received_clock'] = {'passed': True, 'ticks': clock['ticks'],
                                        'measured_bpm': clock['measured_bpm'], 'measurement': 'host arrival'}
    post('studio/connect/keyboard')
    post('ports/input/select', {'port_name': 'PulseStage Keyboard'})
    post('studio/note', {'note': 60, 'channel': 2, 'velocity': 100, 'on': True})
    post('studio/note', {'note': 60, 'channel': 2, 'velocity': 100, 'on': False})
    time.sleep(.15)
    messages = get('monitor/messages')['messages']
    notes = [m['raw_bytes'] for m in messages if m['direction'] == 'RX' and m['message_type'] in ('NOTE_ON', 'NOTE_OFF')]
    assert notes[-2:] == [[145, 60, 100], [129, 60, 0]], notes[-2:]
    results['tests']['integrated_keybed'] = {'passed': True, 'received': notes[-2:]}
    response = requests.post(BASE + 'studio/note', json={'note': 128, 'on': True}, timeout=4)
    assert response.status_code == 422
    results['tests']['invalid_note_rejected'] = {'passed': True, 'status': response.status_code}
    results['passed'] = True
finally:
    try:
        post('clock/stop')
        post('studio/release')
    finally:
        dest = Path(__file__).parent / 'evidence' / 'native-smoke-results.json'
        dest.parent.mkdir(exist_ok=True)
        dest.write_text(json.dumps(results, indent=2), encoding='utf-8')
print(json.dumps(results, indent=2))
