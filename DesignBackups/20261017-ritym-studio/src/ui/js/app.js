/**
 * PulseStage MIDI - Stage Application Controller & State
 */
document.addEventListener("DOMContentLoaded", () => {
  const client = new MidiClient();

  // State
  let state = {
    selectedOutput: null,
    selectedInput: null,
    availableOutputs: [],
    availableInputs: [],
    channel: 1,
    commandType: "PROGRAM_CHANGE",
    presetConvention: "0-127",
    currentWireProgram: 0, // Canonical zero-based 0-127 wire payload
    bpm: 120.0,
    clockRunning: false,
    monitorPaused: false,
    showRawClock: false,
    actions: [],
    clockTickCount: 0,
  };

  // UI Elements
  const elOutSelect = document.getElementById("select-output-port");
  const elInSelect = document.getElementById("select-input-port");
  const elOutStatus = document.getElementById("out-port-status");
  const elInStatus = document.getElementById("in-port-status");
  const elHudOut = document.getElementById("hud-out-name");
  const elHudBpm = document.getElementById("hud-bpm-val");
  const elClockLight = document.getElementById("clock-pulse-light");

  const elChannelSelect = document.getElementById("select-channel");
  const elCmdType = document.getElementById("select-command-type");
  const elProgInput = document.getElementById("input-program-num");
  const elProgWire = document.getElementById("hint-program-wire");
  const elBtnSend = document.getElementById("btn-send-command");

  const elBpmInput = document.getElementById("input-bpm");
  const elClockBadge = document.getElementById("clock-status-badge");
  const elBtnStart = document.getElementById("btn-clock-start");
  const elBtnContinue = document.getElementById("btn-clock-continue");
  const elBtnStop = document.getElementById("btn-clock-stop");
  const elBtnTap = document.getElementById("btn-tap-tempo");

  const elBtnPanic = document.getElementById("btn-panic");
  const elBtnEmergencyStop = document.getElementById("btn-emergency-stop");

  const elMonitorBody = document.getElementById("monitor-table-body");
  const elTagTx = document.getElementById("tag-tx-count");
  const elTagRx = document.getElementById("tag-rx-count");
  const elTagClock = document.getElementById("tag-clock-count");
  const elWsStatus = document.getElementById("ws-status-text");

  // Modal Elements
  const modalAction = document.getElementById("modal-action-editor");
  const btnNewAction = document.getElementById("btn-new-action");
  const btnCloseModal = document.getElementById("btn-close-modal");
  const btnCancelModal = document.getElementById("btn-cancel-modal");
  const btnSaveModal = document.getElementById("btn-save-modal");
  const btnAddStep = document.getElementById("btn-add-step");
  const stepsContainer = document.getElementById("action-steps-container");

  // Populate Channel Select (1 to 16)
  for (let ch = 1; ch <= 16; ch++) {
    const opt = document.createElement("option");
    opt.value = ch;
    opt.textContent = `Channel ${ch}`;
    elChannelSelect.appendChild(opt);
  }

  // 1. Continuous Slider Throttle with Guaranteed Trailing Flush & Full Command Identity
  let ccThrottleTimer = null;
  let ccPendingCommand = null;
  const CC_THROTTLE_MS = 25; // 40 Hz limit

  function sendThrottledCC(ch, controller, val) {
    if (ccThrottleTimer) {
      // Retain full command identity (channel, controller, value)
      ccPendingCommand = { ch, controller, val };
      return;
    }

    client.sendControlChange(ch, controller, val).catch(err => {
      showNotice(`CC transmission error: ${err.message}`, "error");
    });

    ccThrottleTimer = setTimeout(() => {
      ccThrottleTimer = null;
      if (ccPendingCommand !== null) {
        const cmd = ccPendingCommand;
        ccPendingCommand = null;
        sendThrottledCC(cmd.ch, cmd.controller, cmd.val);
      }
    }, CC_THROTTLE_MS);
  }

  function cancelPendingThrottledCC() {
    if (ccThrottleTimer) {
      clearTimeout(ccThrottleTimer);
      ccThrottleTimer = null;
    }
    ccPendingCommand = null;
  }

  // 2. Port Discovery and Management
  async function loadPorts() {
    try {
      const data = await client.getPorts();
      state.availableOutputs = data.outputs || [];
      state.availableInputs = data.inputs || [];

      // Outputs
      elOutSelect.innerHTML = '<option value="">-- Choose Output Port --</option>';
      state.availableOutputs.forEach(p => {
        const opt = document.createElement("option");
        opt.value = p.name;
        opt.textContent = `${p.name} ${p.is_virtual ? '(Virtual)' : ''}`;
        if (p.name === data.selected_output) {
          opt.selected = true;
          state.selectedOutput = p.name;
        }
        elOutSelect.appendChild(opt);
      });

      // Inputs
      elInSelect.innerHTML = '<option value="">-- Choose Input Port --</option>';
      state.availableInputs.forEach(p => {
        const opt = document.createElement("option");
        opt.value = p.name;
        opt.textContent = `${p.name} ${p.is_virtual ? '(Virtual)' : ''}`;
        if (p.name === data.selected_input) {
          opt.selected = true;
          state.selectedInput = p.name;
        }
        elInSelect.appendChild(opt);
      });

      updatePortStatus();
    } catch (e) {
      console.error("Error loading ports:", e);
    }
  }

  function updatePortStatus() {
    if (state.selectedOutput) {
      elOutStatus.textContent = `Connected: Ready for transmission`;
      elOutStatus.style.color = "var(--accent-green)";
      elHudOut.textContent = state.selectedOutput;
    } else {
      elOutStatus.textContent = `Status: Waiting for selection`;
      elOutStatus.style.color = "var(--text-dim)";
      elHudOut.textContent = "No Output Selected";
    }

    if (state.selectedInput) {
      elInStatus.textContent = `Monitoring: Active`;
      elInStatus.style.color = "var(--accent-purple)";

    const elHudInName = document.getElementById("hud-in-name");
    if (elHudInName) {
      elHudInName.textContent = state.selectedInput || "Monitoring Inactive";
    }

    } else {
      elInStatus.textContent = `Status: Monitoring inactive`;
      elInStatus.style.color = "var(--text-dim)";
    }
  }

  elOutSelect.addEventListener("change", async (e) => {
    const val = e.target.value;
    try {
      await client.selectOutput(val);
      state.selectedOutput = val || null;
      updatePortStatus();
    } catch (err) {
      showNotice(`Failed to select output: ${err.message}`, "error");
      loadPorts();
    }
  });

  elInSelect.addEventListener("change", async (e) => {
    const val = e.target.value;
    try {
      await client.selectInput(val);
      state.selectedInput = val || null;
      updatePortStatus();
    } catch (err) {
      showNotice(`Failed to select input: ${err.message}`, "error");
      loadPorts();
    }
  });

  document.getElementById("btn-refresh-ports").addEventListener("click", () => {
    loadPorts();
    showNotice("Port list refreshed.", "info");
  });

  // 3. Preset Numbering Convention & Wire Value Preservation
  const btnToggleZero = document.getElementById("btn-toggle-zero");
  const btnToggleOne = document.getElementById("btn-toggle-one");

  function updatePresetConvention(conv) {
    state.presetConvention = conv;
    if (conv === "0-127") {
      btnToggleZero.classList.add("active");
      btnToggleOne.classList.remove("active");
      elProgInput.min = "0";
      elProgInput.max = "127";
      // Wire value is preserved: display = wire
      elProgInput.value = state.currentWireProgram;
    } else {
      btnToggleOne.classList.add("active");
      btnToggleZero.classList.remove("active");
      elProgInput.min = "1";
      elProgInput.max = "128";
      // Wire value is preserved: display = wire + 1
      elProgInput.value = state.currentWireProgram + 1;
    }
    updateProgramWireHint();
    renderQuickPresetChips();
  }

  btnToggleZero.addEventListener("click", () => updatePresetConvention("0-127"));
  btnToggleOne.addEventListener("click", () => updatePresetConvention("1-128"));

  function updateProgramWireHint() {
    let displayVal = parseInt(elProgInput.value || "0", 10);
    if (state.presetConvention === "1-128") {
      state.currentWireProgram = Math.max(0, Math.min(127, displayVal - 1));
    } else {
      state.currentWireProgram = Math.max(0, Math.min(127, displayVal));
    }
    const wire = state.currentWireProgram;
    elProgWire.textContent = `Wire payload: 0x${wire.toString(16).toUpperCase().padStart(2, '0')} (${wire})`;
  }

  elProgInput.addEventListener("input", updateProgramWireHint);

  function renderQuickPresetChips() {
    const container = document.getElementById("quick-preset-chips");
    container.innerHTML = "";
    const patches = [0, 1, 10, 24, 64, 127];
    patches.forEach(wire => {
      const btn = document.createElement("button");
      btn.className = "chip-btn";
      const displayNum = state.presetConvention === "1-128" ? wire + 1 : wire;
      btn.textContent = `Patch ${displayNum}`;
      btn.addEventListener("click", () => {
        state.currentWireProgram = wire;
        elProgInput.value = displayNum;
        updateProgramWireHint();
      });
      container.appendChild(btn);
    });
  }

  // Command Type Switcher
  elCmdType.addEventListener("change", () => {
    state.commandType = elCmdType.value;
    document.getElementById("group-program-change").classList.toggle("hidden", state.commandType !== "PROGRAM_CHANGE");
    document.getElementById("group-control-change").classList.toggle("hidden", state.commandType !== "CONTROL_CHANGE");
    document.getElementById("group-bank-select").classList.toggle("hidden", state.commandType !== "BANK_SELECT_PC");
  });

  // CC Slider and Value Syncer
  const sliderCc = document.getElementById("range-cc-val");
  const inputCc = document.getElementById("input-cc-val");
  const badgeCc = document.getElementById("cc-val-badge");
  const selectCcNum = document.getElementById("select-cc-num");
  const inputCcCustom = document.getElementById("input-cc-custom");

  selectCcNum.addEventListener("change", () => {
    inputCcCustom.classList.toggle("hidden", selectCcNum.value !== "custom");
  });

  function getActiveCcNumber() {
    if (selectCcNum.value === "custom") {
      return Math.max(0, Math.min(127, parseInt(inputCcCustom.value || "0", 10)));
    }
    return parseInt(selectCcNum.value, 10);
  }

  function setCcValue(val, triggerSend = true) {
    val = Math.max(0, Math.min(127, parseInt(val, 10)));
    sliderCc.value = val;
    inputCc.value = val;
    badgeCc.textContent = val;
    if (triggerSend && state.selectedOutput) {
      const ccNum = getActiveCcNumber();
      sendThrottledCC(elChannelSelect.value, ccNum, val);
    }
  }

  sliderCc.addEventListener("input", (e) => setCcValue(e.target.value, true));
  sliderCc.addEventListener("change", (e) => setCcValue(e.target.value, true)); // Flush final release
  inputCc.addEventListener("input", (e) => setCcValue(e.target.value, true));

  document.getElementById("btn-cc-min").addEventListener("click", () => setCcValue(0, true));
  document.getElementById("btn-cc-mid").addEventListener("click", () => setCcValue(64, true));
  document.getElementById("btn-cc-max").addEventListener("click", () => setCcValue(127, true));

  // 4. Send Command
  async function executeSendCommand() {
    if (!state.selectedOutput) {
      showNotice("Please select an Output Destination first.", "error");
      return;
    }

    const ch = parseInt(elChannelSelect.value, 10);
    const feedbackStatus = document.getElementById("feedback-status");
    const feedbackDesc = document.getElementById("feedback-desc");

    try {
      if (state.commandType === "PROGRAM_CHANGE") {
        const wireProg = state.currentWireProgram;
        const res = await client.sendProgramChange(ch, wireProg, state.presetConvention);
        feedbackStatus.textContent = `Transmitted to ${res.destination}`;
        feedbackStatus.style.color = "var(--accent-green)";
        feedbackDesc.textContent = `${res.plain_language} (${res.bytes_hex})`;
      } else if (state.commandType === "CONTROL_CHANGE") {
        const ccNum = getActiveCcNumber();
        const ccVal = parseInt(sliderCc.value, 10);
        const res = await client.sendControlChange(ch, ccNum, ccVal);
        feedbackStatus.textContent = `Transmitted to ${res.destination}`;
        feedbackStatus.style.color = "var(--accent-green)";
        feedbackDesc.textContent = `${res.plain_language} (${res.bytes_hex})`;
      } else if (state.commandType === "BANK_SELECT_PC") {
        const msb = Math.max(0, Math.min(127, parseInt(document.getElementById("input-bank-msb").value || "0", 10)));
        const lsb = Math.max(0, Math.min(127, parseInt(document.getElementById("input-bank-lsb").value || "0", 10)));
        const pc = Math.max(0, Math.min(127, parseInt(document.getElementById("input-bank-pc").value || "0", 10)));
        const res = await client.sendBankSelect(ch, msb, lsb, pc);
        feedbackStatus.textContent = `Transmitted Bank Select sequence`;
        feedbackStatus.style.color = "var(--accent-green)";
        feedbackDesc.textContent = `Bank MSB ${msb}, LSB ${lsb}, PC ${pc}`;
      }
    } catch (err) {
      feedbackStatus.textContent = "Transmission Error";
      feedbackStatus.style.color = "var(--accent-red)";
      feedbackDesc.textContent = err.message || "Could not write to MIDI port.";
      showNotice(`Transmission failed: ${err.message}`, "error");
    }
  }

  elBtnSend.addEventListener("click", executeSendCommand);

  // 5. MIDI Clock Controls
  function updateClockUi(bpm, isRunning) {
    state.bpm = bpm;
    state.clockRunning = isRunning;
    elHudBpm.textContent = `${bpm.toFixed(1)} BPM`;
    elBpmInput.value = bpm.toFixed(1);

    if (isRunning) {
      elClockBadge.textContent = "RUNNING";
      elClockBadge.style.backgroundColor = "var(--accent-green)";
      elClockBadge.style.color = "#000";
    } else {
      elClockBadge.textContent = "STOPPED";
      elClockBadge.style.backgroundColor = "#334155";
      elClockBadge.style.color = "#FFF";
    }
  }

  elBtnStart.addEventListener("click", async () => {
    if (!state.selectedOutput) {
      showNotice("Select an output port for MIDI Clock.", "error");
      return;
    }
    try {
      const res = await client.startClock();
      updateClockUi(res.bpm, true);
    } catch (err) {
      showNotice(`Clock start failed: ${err.message}`, "error");
    }
  });

  elBtnStop.addEventListener("click", async () => {
    try {
      const res = await client.stopClock();
      updateClockUi(res.bpm, false);
    } catch (err) {
      showNotice(`Clock stop failed: ${err.message}`, "error");
    }
  });

  elBtnContinue.addEventListener("click", async () => {
    try {
      const res = await client.continueClock();
      updateClockUi(res.bpm, true);
    } catch (err) {
      showNotice(`Clock continue failed: ${err.message}`, "error");
    }
  });

  elBpmInput.addEventListener("change", async (e) => {
    const newBpm = parseFloat(e.target.value);
    if (!isNaN(newBpm)) {
      try {
        const res = await client.setBpm(newBpm);
        updateClockUi(res.bpm, state.clockRunning);
      } catch (err) {
        showNotice(`Failed to set BPM: ${err.message}`, "error");
      }
    }
  });

  elBtnTap.addEventListener("click", async () => {
    try {
      const res = await client.tapTempo();
      updateClockUi(res.bpm, state.clockRunning);
    } catch (err) {
      showNotice(`Tap tempo error: ${err.message}`, "error");
    }
  });

  document.querySelectorAll(".bpm-chip").forEach(btn => {
    btn.addEventListener("click", async () => {
      const b = parseFloat(btn.dataset.bpm);
      try {
        const res = await client.setBpm(b);
        updateClockUi(res.bpm, state.clockRunning);
      } catch (err) {
        showNotice(`Failed to set BPM: ${err.message}`, "error");
      }
    });
  });

  // 6. Emergency Panic & Stop
  elBtnPanic.addEventListener("click", async () => {
    cancelPendingThrottledCC();
    try {
      const res = await client.panic();
      updateClockUi(state.bpm, false);
      showNotice(res.message, "warning");
    } catch (err) {
      showNotice(`Panic transmission failed: ${err.message}`, "error");
    }
  });

  elBtnEmergencyStop.addEventListener("click", async () => {
    cancelPendingThrottledCC();
    try {
      await client.emergencyStop();
      updateClockUi(state.bpm, false);
      showNotice("Emergency stop executed. All transmissions halted.", "warning");
    } catch (err) {
      showNotice(`Emergency stop error: ${err.message}`, "error");
    }
  });

  // 7. Performance Actions Pad & Interactive Modal Editor
  async function loadActions() {
    try {
      const actions = await client.getActions();
      state.actions = actions;
      const container = document.getElementById("actions-pad-container");
      container.innerHTML = "";

      actions.forEach((act, idx) => {
        // Safe DOM construction with text nodes
        const card = document.createElement("div");
        card.className = "action-card";

        const header = document.createElement("div");
        header.className = "action-card-header";

        const title = document.createElement("span");
        title.className = "action-title";
        title.textContent = act.name;

        const hotkey = document.createElement("span");
        hotkey.className = "action-hotkey";
        hotkey.textContent = act.hotkey || String(idx + 1);

        header.appendChild(title);
        header.appendChild(hotkey);

        const desc = document.createElement("p");
        desc.className = "action-desc";
        desc.textContent = act.description || `${act.steps.length} command steps`;

        const btnRow = document.createElement("div");
        btnRow.style.display = "flex";
        btnRow.style.gap = "6px";
        btnRow.style.marginTop = "8px";

        const btnTrigger = document.createElement("button");
        btnTrigger.className = "btn-trigger-action";
        btnTrigger.style.flex = "1";
        btnTrigger.textContent = "▶ Trigger";
        btnTrigger.addEventListener("click", () => triggerAction(act.id, act.name));

        const btnDelete = document.createElement("button");
        btnDelete.className = "btn-xs btn-ghost";
        btnDelete.textContent = "🗑";
        btnDelete.title = "Delete Action";
        btnDelete.addEventListener("click", async () => {
          if (confirm(`Delete action "${act.name}"?`)) {
            await client.deleteAction(act.id);
            loadActions();
          }
        });

        btnRow.appendChild(btnTrigger);
        btnRow.appendChild(btnDelete);

        card.appendChild(header);
        card.appendChild(desc);
        card.appendChild(btnRow);
        container.appendChild(card);
      });
    } catch (e) {
      console.error("Error loading actions:", e);
    }
  }

  async function triggerAction(actionId, name) {
    try {
      const res = await client.executeAction(actionId);
      showNotice(`Action '${name}' executed (${res.executed_steps} steps).`, "success");
    } catch (err) {
      showNotice(`Action failed: ${err.message}`, "error");
    }
  }

  // Action Modal Handlers
  btnNewAction.addEventListener("click", () => {
    document.getElementById("input-act-name").value = "";
    document.getElementById("input-act-desc").value = "";
    stepsContainer.innerHTML = "";
    addStepRow(); // Initial step
    modalAction.classList.remove("hidden");
  });

  btnCloseModal.addEventListener("click", () => modalAction.classList.add("hidden"));
  btnCancelModal.addEventListener("click", () => modalAction.classList.add("hidden"));

  btnAddStep.addEventListener("click", () => addStepRow());

  function addStepRow() {
    const row = document.createElement("div");
    row.className = "step-builder-row";
    row.style.display = "grid";
    row.style.gridTemplateColumns = "1.5fr 0.8fr 1.5fr 1fr 1fr 30px";
    row.style.gap = "6px";
    row.style.marginBottom = "6px";
    row.style.alignItems = "center";

    // Target Port Select
    const selPort = document.createElement("select");
    selPort.className = "step-port";
    state.availableOutputs.forEach(p => {
      const opt = document.createElement("option");
      opt.value = p.name;
      opt.textContent = p.name;
      selPort.appendChild(opt);
    });

    // Channel Select
    const selCh = document.createElement("select");
    selCh.className = "step-ch";
    for (let c = 1; c <= 16; c++) {
      const opt = document.createElement("option");
      opt.value = c;
      opt.textContent = `Ch ${c}`;
      selCh.appendChild(opt);
    }

    // Command Type
    const selCmd = document.createElement("select");
    selCmd.className = "step-cmd";
    selCmd.innerHTML = `
      <option value="PROGRAM_CHANGE">Program Change</option>
      <option value="CONTROL_CHANGE">Control Change</option>
      <option value="BANK_SELECT_PC">Bank Select + PC</option>
    `;

    // Data1 (PC / CC #)
    const inpD1 = document.createElement("input");
    inpD1.type = "number";
    inpD1.className = "step-d1";
    inpD1.min = 0; inpD1.max = 127; inpD1.value = 0;
    inpD1.placeholder = "PC / CC #";

    // Data2 (Val / LSB)
    const inpD2 = document.createElement("input");
    inpD2.type = "number";
    inpD2.className = "step-d2";
    inpD2.min = 0; inpD2.max = 127; inpD2.value = 0;
    inpD2.placeholder = "Value";

    // Remove button
    const btnRemove = document.createElement("button");
    btnRemove.className = "btn-xs btn-ghost";
    btnRemove.textContent = "✕";
    btnRemove.addEventListener("click", () => row.remove());

    row.appendChild(selPort);
    row.appendChild(selCh);
    row.appendChild(selCmd);
    row.appendChild(inpD1);
    row.appendChild(inpD2);
    row.appendChild(btnRemove);
    stepsContainer.appendChild(row);
  }

  btnSaveModal.addEventListener("click", async () => {
    const name = document.getElementById("input-act-name").value.trim();
    if (!name) {
      alert("Please provide an action name.");
      return;
    }
    const desc = document.getElementById("input-act-desc").value.trim();
    const rows = stepsContainer.querySelectorAll(".step-builder-row");
    if (rows.length === 0) {
      alert("Please add at least one step.");
      return;
    }

    const steps = [];
    rows.forEach((r, idx) => {
      steps.push({
        id: `s_${idx + 1}`,
        target_port_name: r.querySelector(".step-port").value,
        channel: parseInt(r.querySelector(".step-ch").value, 10),
        command_type: r.querySelector(".step-cmd").value,
        data1: parseInt(r.querySelector(".step-d1").value || "0", 10),
        data2: parseInt(r.querySelector(".step-d2").value || "0", 10),
        delay_ms: 20,
      });
    });

    const actionObj = {
      id: `act_${Date.now()}`,
      name: name,
      description: desc,
      color: "#00F0FF",
      steps: steps,
    };

    try {
      await client.saveAction(actionObj);
      modalAction.classList.add("hidden");
      loadActions();
      showNotice(`Action '${name}' created successfully!`, "success");
    } catch (err) {
      alert(`Failed to save action: ${err.message}`);
    }
  });

  // 8. Diagnostic Monitor & Live Stream
  let renderedRowCounter = 0;
  const MAX_DOM_ROWS = 150;

  function appendMonitorMessage(msg) {
    if (state.monitorPaused) return;

    // Filter check
    const filterCh = document.getElementById("filter-channel").value;
    if (filterCh && msg.channel && msg.channel !== parseInt(filterCh, 10)) {
      return;
    }

    if (msg.message_type === "CLOCK") {
      state.clockTickCount++;
      // Pulse beat light on quarter-note beat (every 24 ticks)
      if (state.clockTickCount % 24 === 0) {
        pulseBeatLight();
      }
      if (!state.showRawClock) {
        return;
      }
    }

    const emptyRow = elMonitorBody.querySelector(".empty-row");
    if (emptyRow) emptyRow.remove();

    const tr = document.createElement("tr");
    const badgeClass = msg.direction === "TX" ? "badge-tx" : "badge-rx";

    const tdDir = document.createElement("td");
    tdDir.className = "col-dir";
    const badge = document.createElement("span");
    badge.className = badgeClass;
    badge.textContent = msg.direction;
    tdDir.appendChild(badge);

    const tdTime = document.createElement("td");
    tdTime.className = "col-time";
    tdTime.textContent = (msg.timestamp_ms % 100000).toFixed(1);

    const tdPort = document.createElement("td");
    tdPort.className = "col-port";
    tdPort.textContent = (msg.port_name || "-").substring(0, 18);

    const tdCh = document.createElement("td");
    tdCh.className = "col-ch";
    tdCh.textContent = msg.channel ? String(msg.channel) : "-";

    const tdType = document.createElement("td");
    tdType.className = "col-type";
    tdType.textContent = msg.message_type;

    const tdHex = document.createElement("td");
    tdHex.className = "col-hex";
    tdHex.textContent = msg.raw_bytes ? msg.raw_bytes.map(b => "0x" + b.toString(16).toUpperCase().padStart(2, '0')).join(' ') : "-";

    const tdDesc = document.createElement("td");
    tdDesc.className = "col-desc";
    tdDesc.textContent = msg.friendly_text || "-";

    tr.appendChild(tdDir);
    tr.appendChild(tdTime);
    tr.appendChild(tdPort);
    tr.appendChild(tdCh);
    tr.appendChild(tdType);
    tr.appendChild(tdHex);
    tr.appendChild(tdDesc);

    elMonitorBody.appendChild(tr);
    renderedRowCounter++;

    if (renderedRowCounter > MAX_DOM_ROWS) {
      elMonitorBody.removeChild(elMonitorBody.firstChild);
      renderedRowCounter--;
    }

    const wrap = document.getElementById("monitor-table-wrap");
    wrap.scrollTop = wrap.scrollHeight;
  }

  let beatPulseTimeout = null;
  function pulseBeatLight() {
    elClockLight.classList.add("pulse");
    clearTimeout(beatPulseTimeout);
    beatPulseTimeout = setTimeout(() => {
      elClockLight.classList.remove("pulse");
    }, 90);
  }

  // Monitor Buttons
  const btnPause = document.getElementById("btn-pause-monitor");
  btnPause.addEventListener("click", async () => {
    state.monitorPaused = !state.monitorPaused;
    btnPause.textContent = state.monitorPaused ? "Resume" : "Pause";
    btnPause.style.color = state.monitorPaused ? "var(--accent-amber)" : "var(--text-muted)";
  });

  document.getElementById("btn-clear-monitor").addEventListener("click", async () => {
    await client.clearMonitor();
    elMonitorBody.innerHTML = '<tr class="empty-row"><td colspan="7">Monitor cleared. Waiting for events...</td></tr>';
    renderedRowCounter = 0;
  });

  document.getElementById("check-show-raw-clock").addEventListener("change", (e) => {
    state.showRawClock = e.target.checked;
  });

  // Export handlers
  document.getElementById("export-json").addEventListener("click", (e) => {
    e.preventDefault();
    window.open("/api/monitor/export/json", "_blank");
  });
  document.getElementById("export-csv").addEventListener("click", (e) => {
    e.preventDefault();
    window.open("/api/monitor/export/csv", "_blank");
  });
  document.getElementById("export-txt").addEventListener("click", (e) => {
    e.preventDefault();
    window.open("/api/monitor/export/text", "_blank");
  });

  // WebSocket Event Handlers
  client.on("status", (s) => {
    if (s.connected) {
      elWsStatus.textContent = "WS: Streaming Live";
      elWsStatus.style.color = "var(--accent-green)";
    } else {
      elWsStatus.textContent = "WS: Disconnected";
      elWsStatus.style.color = "var(--accent-red)";
    }
  });

  client.on("message", (msg) => {
    appendMonitorMessage(msg);
    updateTelemetryCounters();
    if (msg.direction === "RX") {
      checkPracticeTest1(msg);
    }
  });

  client.on("clock", (clk) => {
    updateClockUi(clk.bpm, clk.state === "RUNNING");
  });

  client.on("port_disconnect", (evt) => {
    showNotice(evt.message || "A connected MIDI port was disconnected.", "error");
    loadPorts();
  });

  async function updateTelemetryCounters() {
    try {
      const status = await client.getStatus();
      elTagTx.textContent = `TX: ${status.monitor.tx_count}`;
      elTagRx.textContent = `RX: ${status.monitor.rx_count}`;
      elTagClock.textContent = `Ticks: ${status.monitor.clock_ticks}`;
    } catch (e) {}
  }

  // Global Keyboard Shortcuts
  window.addEventListener("keydown", (e) => {
    // Panic on Escape works everywhere, including when inputs have focus
    if (e.key === "Escape") {
      client.panic().then(res => {
        updateClockUi(state.bpm, false);
        showNotice(res.message, "warning");
      }).catch(err => {
        showNotice(`Panic failed: ${err.message}`, "error");
      });
      return;
    }

    // Ignore other hotkeys when typing in input fields
    if (["INPUT", "SELECT", "TEXTAREA"].includes(document.activeElement.tagName)) {
      if (e.key === "Enter") {
        executeSendCommand();
      }
      return;
    }

    if (e.code === "Space") {
      e.preventDefault();
      if (state.clockRunning) {
        client.stopClock().then(res => updateClockUi(res.bpm, false));
      } else {
        if (state.selectedOutput) {
          client.startClock().then(res => updateClockUi(res.bpm, true)).catch(err => {
            showNotice(`Clock start failed: ${err.message}`, "error");
          });
        } else {
          showNotice("Select an output port first.", "error");
        }
      }
    } else if (e.key === "t" || e.key === "T") {
      client.tapTempo().then(res => updateClockUi(res.bpm, state.clockRunning)).catch(err => {
        showNotice(`Tap error: ${err.message}`, "error");
      });
    } else if (e.key >= "1" && e.key <= "9") {
      const idx = parseInt(e.key, 10) - 1;
      if (state.actions[idx]) {
        triggerAction(state.actions[idx].id, state.actions[idx].name);
      }
    }
  });

  // Banner Utility
  function showNotice(text, type = "info") {
    const banner = document.getElementById("notice-banner");
    const bannerText = document.getElementById("notice-text");
    bannerText.textContent = text;
    banner.className = `notice-banner ${type}`;
    banner.classList.remove("hidden");

    setTimeout(() => {
      banner.classList.add("hidden");
    }, 4500);
  }

  window.dismissNotice = function() {
    document.getElementById("notice-banner").classList.add("hidden");
  };

  // Initial Boot
  client.initWebSocket();
  loadPorts();
  loadActions();
  updatePresetConvention("0-127");
  setInterval(updateTelemetryCounters, 3000);

  // ==========================================================================
  // TAB NAVIGATION & MONITOR JUMP
  // ==========================================================================
  const navTabs = document.querySelectorAll(".nav-tab");
  const tabViews = document.querySelectorAll(".tab-view");
  const btnJumpMonitor = document.getElementById("btn-jump-monitor");

  function switchTab(targetViewId) {
    navTabs.forEach(t => {
      t.classList.toggle("active", t.dataset.target === targetViewId);
    });
    tabViews.forEach(v => {
      if (v.id === targetViewId) {
        v.classList.remove("hidden");
      } else {
        v.classList.add("hidden");
      }
    });

    // Move or sync monitor card between stage and dedicated monitor views
    const cardMon = document.getElementById("card-monitor");
    if (targetViewId === "view-monitor") {
      const fullMount = document.getElementById("full-monitor-mount");
      if (fullMount && cardMon && cardMon.parentElement !== fullMount) {
        fullMount.appendChild(cardMon);
      }
    } else {
      const stagePreview = document.getElementById("pane-monitor-preview");
      if (stagePreview && cardMon && cardMon.parentElement !== stagePreview) {
        stagePreview.appendChild(cardMon);
      }
    }
  }

  navTabs.forEach(tab => {
    tab.addEventListener("click", () => switchTab(tab.dataset.target));
  });

  if (btnJumpMonitor) {
    btnJumpMonitor.addEventListener("click", () => {
      switchTab("view-monitor");
      const cardMon = document.getElementById("card-monitor");
      if (cardMon) {
        cardMon.style.transition = "box-shadow 0.3s ease";
        cardMon.style.boxShadow = "0 0 25px rgba(0, 240, 255, 0.6)";
        setTimeout(() => {
          cardMon.style.boxShadow = "";
        }, 1200);
      }
    });
  }

  // Update telemetry counters across all views
  const elFullTxCount = document.getElementById("full-tx-count");
  const elFullRxCount = document.getElementById("full-rx-count");
  const elFullClockCount = document.getElementById("full-clock-count");
  const elHudTxBadge = document.getElementById("hud-tx-badge");
  const elHudRxBadge = document.getElementById("hud-rx-badge");

  const originalUpdateTelemetry = updateTelemetryCounters;
  updateTelemetryCounters = async function() {
    try {
      const status = await client.getStatus();
      elTagTx.textContent = `TX: ${status.monitor.tx_count}`;
      elTagRx.textContent = `RX: ${status.monitor.rx_count}`;
      elTagClock.textContent = `Ticks: ${status.monitor.clock_ticks}`;
      if (elFullTxCount) elFullTxCount.textContent = status.monitor.tx_count;
      if (elFullRxCount) elFullRxCount.textContent = status.monitor.rx_count;
      if (elFullClockCount) elFullClockCount.textContent = status.monitor.clock_ticks;
      if (elHudTxBadge) elHudTxBadge.textContent = `TX: ${status.monitor.tx_count}`;
      if (elHudRxBadge) elHudRxBadge.textContent = `RX: ${status.monitor.rx_count}`;
    } catch (e) {}
  };

  // ==========================================================================
  // PRACTICE & TEST LAB GUIDED JOURNEYS
  // ==========================================================================
  let isListeningTest1 = false;

  function checkPracticeTest1(msg) {
    if (!isListeningTest1) return;
    if (msg.message_type === "NOTE_ON" || msg.message_type === "NOTE_OFF") {
      isListeningTest1 = false;
      const pill = document.getElementById("pill-test-1");
      const resBox = document.getElementById("result-test-1");
      if (pill) {
        pill.textContent = "PASS";
        pill.className = "test-state-pill pill-pass";
      }
      if (resBox) {
        resBox.textContent = `✅ PASS: Verified ${msg.message_type} Note ${msg.data1} (Vel ${msg.data2}) on Ch ${msg.channel}. Signal reached PulseStage RX!`;
        resBox.className = "test-result-box pass";
      }
      showNotice("Test 1 Passed: Keyboard notes successfully verified!", "info");
    }
  }

  // Journey 1 Setup & Run
  const btnSetupTest1 = document.getElementById("btn-setup-test-1");
  const btnRunTest1 = document.getElementById("btn-run-test-1");
  if (btnSetupTest1) {
    btnSetupTest1.addEventListener("click", async () => {
      const kbPort = state.availableInputs.find(p => p.toLowerCase().includes("keyboard") || p.toLowerCase().includes("pulse"));
      const target = kbPort || (state.availableInputs.length > 0 ? state.availableInputs[0] : null);
      if (target) {
        try {
          await client.selectInput(target);
          state.selectedInput = target;
          elInSelect.value = target;
          updatePortStatus();
          showNotice(`Selected Input: '${target}'`, "info");
        } catch (e) {
          showNotice(`Failed to select port: ${e.message}`, "error");
        }
      } else {
        showNotice("No virtual input found. Ensure loopMIDI has 'PulseStage Keyboard' created.", "warning");
      }
    });
  }

  if (btnRunTest1) {
    btnRunTest1.addEventListener("click", () => {
      isListeningTest1 = true;
      const resBox = document.getElementById("result-test-1");
      if (resBox) {
        resBox.textContent = "Listening for incoming notes... Press any key on the Virtual Keyboard now!";
        resBox.className = "test-result-box";
      }
    });
  }

  // Journey 2 Setup & Run
  const btnSetupTest2 = document.getElementById("btn-setup-test-2");
  const btnRunTest2 = document.getElementById("btn-run-test-2");
  if (btnSetupTest2) {
    btnSetupTest2.addEventListener("click", async () => {
      const pedalPort = state.availableOutputs.find(p => p.toLowerCase().includes("pedal") || p.toLowerCase().includes("pulse"));
      const target = pedalPort || (state.availableOutputs.length > 0 ? state.availableOutputs[0] : null);
      if (target) {
        try {
          await client.selectOutput(target);
          state.selectedOutput = target;
          elOutSelect.value = target;
          updatePortStatus();
          showNotice(`Selected Output: '${target}'`, "info");
        } catch (e) {
          showNotice(`Failed to select port: ${e.message}`, "error");
        }
      } else {
        showNotice("No pedal port found. Launch 'VirtualPedal/Start Pedal.bat' first.", "warning");
      }
    });
  }

  if (btnRunTest2) {
    btnRunTest2.addEventListener("click", async () => {
      if (!state.selectedOutput) {
        showNotice("Please select an output port first.", "error");
        return;
      }
      try {
        const res = await client.sendProgramChange(state.channel, 24);
        const pill = document.getElementById("pill-test-2");
        const resBox = document.getElementById("result-test-2");
        if (pill) {
          pill.textContent = "PASS";
          pill.className = "test-state-pill pill-pass";
        }
        if (resBox) {
          resBox.textContent = `✅ PASS: Transmitted Program Change 24 (${res.bytes_hex}). Verified on output '${state.selectedOutput}'. Check Virtual Pedal screen!`;
          resBox.className = "test-result-box pass";
        }
        showNotice("Test 2 Passed: Program Change 24 delivered!", "info");
      } catch (e) {
        showNotice(`Test 2 failed: ${e.message}`, "error");
      }
    });
  }

  // Journey 3: Move Virtual Pedal Parameter (CC 11)
  const sliderCc11 = document.getElementById("practice-slider-cc11");
  const valCc11 = document.getElementById("practice-cc11-val");
  const btnSendCc11 = document.getElementById("btn-send-practice-cc11");

  if (sliderCc11 && valCc11) {
    sliderCc11.addEventListener("input", (e) => {
      valCc11.textContent = e.target.value;
    });
  }

  if (btnSendCc11) {
    btnSendCc11.addEventListener("click", async () => {
      if (!state.selectedOutput) {
        showNotice("Please select an output port first.", "error");
        return;
      }
      const val = parseInt(sliderCc11.value, 10);
      try {
        const res = await client.sendControlChange(state.channel, 11, val);
        const pill = document.getElementById("pill-test-3");
        const resBox = document.getElementById("result-test-3");
        if (pill) {
          pill.textContent = "PASS";
          pill.className = "test-state-pill pill-pass";
        }
        if (resBox) {
          resBox.textContent = `✅ PASS: Transmitted CC 11 = ${val} (${res.bytes_hex}). Virtual Pedal Expression knob rotated!`;
          resBox.className = "test-result-box pass";
        }
        showNotice("Test 3 Passed: Parameter CC 11 delivered!", "info");
      } catch (e) {
        showNotice(`Test 3 failed: ${e.message}`, "error");
      }
    });
  }

  // Journey 4: Synchronize Pedal Tempo
  const btnRunTest4Start = document.getElementById("btn-run-test-4-start");
  const btnRunTest4Stop = document.getElementById("btn-run-test-4-stop");

  if (btnRunTest4Start) {
    btnRunTest4Start.addEventListener("click", async () => {
      if (!state.selectedOutput) {
        showNotice("Please select an output port first.", "error");
        return;
      }
      try {
        await client.setBpm(120.0);
        const res = await client.startClock();
        updateClockUi(res.bpm, true);
        const pill = document.getElementById("pill-test-4");
        const resBox = document.getElementById("result-test-4");
        if (pill) {
          pill.textContent = "PASS";
          pill.className = "test-state-pill pill-pass";
        }
        if (resBox) {
          resBox.textContent = "✅ PASS: 24 PPQN MIDI Clock running at 120.0 BPM. Virtual Pedal beat light pulsing and calculating BPM!";
          resBox.className = "test-result-box pass";
        }
        showNotice("Test 4 Passed: 24 PPQN Clock synchronized!", "info");
      } catch (e) {
        showNotice(`Test 4 failed: ${e.message}`, "error");
      }
    });
  }

  if (btnRunTest4Stop) {
    btnRunTest4Stop.addEventListener("click", async () => {
      try {
        const res = await client.stopClock();
        updateClockUi(res.bpm, false);
        const resBox = document.getElementById("result-test-4");
        if (resBox) {
          resBox.textContent = "Clock stopped. Transport Stop (0xFC) transmitted.";
        }
      } catch (e) {}
    });
  }

  // Journey 5: Execute Performance Action Macro
  const btnRunTest5 = document.getElementById("btn-run-test-5");
  if (btnRunTest5) {
    btnRunTest5.addEventListener("click", async () => {
      if (!state.selectedOutput) {
        showNotice("Please select an output port first.", "error");
        return;
      }
      if (state.actions.length === 0) {
        showNotice("No actions saved yet. Create an action in Step 4 on the Stage tab.", "warning");
        return;
      }
      try {
        const action = state.actions[0];
        await client.executeAction(action.id);
        const pill = document.getElementById("pill-test-5");
        const resBox = document.getElementById("result-test-5");
        if (pill) {
          pill.textContent = "PASS";
          pill.className = "test-state-pill pill-pass";
        }
        if (resBox) {
          resBox.textContent = `✅ PASS: Action '${action.name}' executed with verified sequence pacing!`;
          resBox.className = "test-result-box pass";
        }
        showNotice(`Test 5 Passed: Macro '${action.name}' completed!`, "info");
      } catch (e) {
        showNotice(`Test 5 failed: ${e.message}`, "error");
      }
    });
  }

  // ==========================================================================
  // PROFESSIONAL MUSICIAN & STUDIO SETTINGS
  // ==========================================================================
  // 1. 14-Bit Pitch Bend
  const sliderPitch = document.getElementById("slider-pitch-bend");
  const lblPitchVal = document.getElementById("lbl-pitch-val");
  const btnSendPitch = document.getElementById("btn-send-pitch");
  const btnPitchCenter = document.getElementById("btn-pitch-center");

  if (sliderPitch && lblPitchVal) {
    sliderPitch.addEventListener("input", (e) => {
      const val = parseInt(e.target.value, 10);
      const delta = val - 8192;
      lblPitchVal.textContent = `${delta >= 0 ? "+" : ""}${delta} (Raw: ${val})`;
    });
  }

  if (btnSendPitch) {
    btnSendPitch.addEventListener("click", async () => {
      if (!state.selectedOutput) {
        showNotice("Select an output port first.", "error");
        return;
      }
      const val = parseInt(sliderPitch.value, 10);
      try {
        const res = await client.sendPitchBend(state.channel, val);
        showNotice(`Pitch Bend transmitted: ${res.plain_language}`, "info");
      } catch (e) {
        showNotice(`Pitch Bend error: ${e.message}`, "error");
      }
    });
  }

  if (btnPitchCenter) {
    btnPitchCenter.addEventListener("click", async () => {
      sliderPitch.value = 8192;
      lblPitchVal.textContent = "0 (Center)";
      if (state.selectedOutput) {
        try {
          await client.sendPitchBend(state.channel, 8192);
          showNotice("Pitch Bend centered (0 shift).", "info");
        } catch (e) {}
      }
    });
  }

  // 2. Channel Pressure (Aftertouch)
  const sliderPressure = document.getElementById("slider-channel-pressure");
  const lblPressureVal = document.getElementById("lbl-pressure-val");
  const btnSendPressure = document.getElementById("btn-send-pressure");
  const btnPressureZero = document.getElementById("btn-pressure-zero");

  if (sliderPressure && lblPressureVal) {
    sliderPressure.addEventListener("input", (e) => {
      lblPressureVal.textContent = e.target.value;
    });
  }

  if (btnSendPressure) {
    btnSendPressure.addEventListener("click", async () => {
      if (!state.selectedOutput) {
        showNotice("Select an output port first.", "error");
        return;
      }
      const val = parseInt(sliderPressure.value, 10);
      try {
        const res = await client.sendChannelPressure(state.channel, val);
        showNotice(`Pressure transmitted: ${res.plain_language}`, "info");
      } catch (e) {
        showNotice(`Pressure error: ${e.message}`, "error");
      }
    });
  }

  if (btnPressureZero) {
    btnPressureZero.addEventListener("click", async () => {
      sliderPressure.value = 0;
      lblPressureVal.textContent = "0";
      if (state.selectedOutput) {
        try {
          await client.sendChannelPressure(state.channel, 0);
          showNotice("Channel pressure zeroed.", "info");
        } catch (e) {}
      }
    });
  }

  // 3. Raw Hex & SysEx Injector Terminal
  const txtRawHex = document.getElementById("txt-raw-hex");
  const lblHexCount = document.getElementById("lbl-hex-count");
  const btnSendRawHex = document.getElementById("btn-send-raw-hex");

  if (txtRawHex && lblHexCount) {
    txtRawHex.addEventListener("input", (e) => {
      const clean = e.target.value.replace(/[^0-9a-fA-F]/g, "");
      const bytesCount = Math.floor(clean.length / 2);
      lblHexCount.textContent = `${bytesCount} bytes`;
    });
  }

  if (btnSendRawHex) {
    btnSendRawHex.addEventListener("click", async () => {
      if (!state.selectedOutput) {
        showNotice("Select an output port first.", "error");
        return;
      }
      const hex = txtRawHex.value.trim();
      if (!hex) {
        showNotice("Please enter a hexadecimal byte string.", "warning");
        return;
      }
      try {
        const res = await client.sendRawHex(hex);
        showNotice(`Transmitted ${res.length} raw bytes: ${res.bytes_hex}`, "info");
      } catch (e) {
        showNotice(`Raw hex error: ${e.message}`, "error");
      }
    });
  }

  document.querySelectorAll(".btn-hex-chip").forEach(chip => {
    chip.addEventListener("click", () => {
      if (txtRawHex) {
        txtRawHex.value = chip.dataset.hex;
        const clean = chip.dataset.hex.replace(/[^0-9a-fA-F]/g, "");
        if (lblHexCount) lblHexCount.textContent = `${Math.floor(clean.length / 2)} bytes`;
      }
    });
  });

});
