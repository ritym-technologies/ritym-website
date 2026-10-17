/* Opt-in renderer/IPC QA. Called only with isolated --verify-desktop arguments. */
(async () => {
  console.info('Desktop QA: awaiting channel');
  const bridge = await window.PulseStageDesktop.ready;
  console.info('Desktop QA: channel ready');
  let messages = 0;
  bridge.midiEvent.connect(raw => {if (JSON.parse(raw).type === 'midi_message') messages++;});
  async function call(path, body) {
    console.info('Desktop QA request: ' + path);
    const response = await fetch('/api/' + path, body === undefined ? {} :
      {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
    const value = await response.json();
    if (!response.ok) throw Error(path + ': ' + JSON.stringify(value));
    return value;
  }
  try {
    const keyboard = await call('studio/connect/keyboard', {});
    if (keyboard.transport_mode !== 'internal') throw Error('Expected internal test transport.');
    await call('ports/input/select', {port_name:keyboard.keyboard_port});
    for (const on of [true, false]) await call('studio/note', {note:60,channel:1,velocity:100,on});
    const pedal = await call('studio/connect/pedal', {});
    await call('ports/output/select', {port_name:pedal.pedal_port});
    await call('send/program-change', {channel:1,program:24});
    await call('send/control-change', {channel:1,controller:11,value:96});
    await call('send/control-change', {channel:1,controller:64,value:127});
    if ((await call('studio/state')).pedal.cc['64'] !== 127) throw Error('Footswitch press was not received.');
    await call('send/control-change', {channel:1,controller:64,value:0});
    if ((await call('studio/state')).pedal.cc['64'] !== 0) throw Error('Footswitch release was not received.');
    await call('clock/bpm', {bpm:120}); await call('clock/start', {});
    await new Promise(resolve => setTimeout(resolve, 2500));
    let received = await call('studio/state');
    const clockDeadline = performance.now() + 4000;
    while ((received.pedal.ticks < 96 || received.pedal.measured_bpm === null || Math.abs(received.pedal.measured_bpm - 120) > 3) && performance.now() < clockDeadline) {
      await new Promise(resolve => setTimeout(resolve,250)); received = await call('studio/state');
    }
    await call('clock/stop', {});
    const status = await call('status');
    if (status.monitor.rx_count !== 2 || received.pedal.program !== 24 || received.pedal.cc['11'] !== 96)
      throw Error('Received note/controller evidence did not match.');
    if (received.pedal.ticks < 96 || Math.abs(received.pedal.measured_bpm - 120) > 3 || messages < 2)
      throw Error('Clock or pushed desktop events were not received: '+JSON.stringify({ticks:received.pedal.ticks,bpm:received.pedal.measured_bpm,messages}));
    if (!document.querySelector('#piano [data-note="60"]')) throw Error('The keybed did not render.');
    bridge.finishCheck(JSON.stringify({passed:true, renderer:'bundled Qt WebEngine',
      bridge:'Qt WebChannel IPC', keyboard_rx:2, program:received.pedal.program,
      expression:received.pedal.cc['11'], ticks:received.pedal.ticks,
      footswitch_press_release:true,
      measured_bpm:received.pedal.measured_bpm, pushed_events:messages,
      clock_stopped:status.clock.state==='STOPPED', scheme:location.protocol,
      http_listener:false, physical_hardware_tested:false}));
  } catch (error) {
    await call('clock/stop', {}).catch(() => {});
    bridge.finishCheck(JSON.stringify({passed:false,error:String(error)}));
  }
})();
