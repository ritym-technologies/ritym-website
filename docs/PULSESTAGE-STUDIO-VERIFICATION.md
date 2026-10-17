# Studio redesign verification — 17 October 2026

## Implemented

Original PulseStage web UI with Dark Console and Light Console, local fonts/assets, responsive sidebar navigation, route strip, explicit-send rotary/numeric composer, master transport, integrated MIDI keybed, actual MIDI-input reference pedal, bounded event monitor, measured controller/clock plots, receipt-based guided tests, pitch/pressure/raw utilities and action create/edit/duplicate/delete/reorder controls.

New backend: `src/api/studio.py`, registered and shut down by `src/api/server.py`. Existing engine routes and separate desktop keyboard/pedal tools are retained. Dark is the initial theme; switching is stored locally in the browser. Static assets have an explicit revision query to avoid stale UI assets after updates.

## Verification performed

* Existing25-test application suite: passed in isolated source/config copy.
* Full suite with8 new tests: **33 passed**, about2.89 seconds. Tests cover original codecs/config/clock/actions/monitor/adapter/streaming plus new received-state, wrong-channel, bounds, native-mode and note-ownership behavior.
* After a final cleanup adjustment to avoid unnecessary idle controller traffic, the8 instrument tests were rerun and passed. JavaScript syntax checks passed.
* Native smoke script: program/bank/CC ordering on channel2; exact expected bytes `C1 18`, `B1 00 01`, `B1 20 02`, `C1 09`, `B1 0B 60`; wrong-output negative test left receiver state unchanged; integrated keybed received `91 3C 64`, `81 3C 00`; invalid note128 rejected with422; clock sample108 ticks with measured120.00 BPM at host arrival. See native-smoke-results.json.
* Browser guided tests: all4 reached **VERIFIED** using actual received events. Clock UI run recorded115 ticks near119.97 BPM and stopped. See guided-ui-results.txt.
* Browser editor: created and saved a temporary one-step action in the isolated preview configuration; did not replace production user actions.
* Browser console warning/error check: none observed during sampled interactions.
* Responsive checks:1440-pixel desktop and900-pixel narrower window; no horizontal overflow at900 pixels. Normal-height windows can scroll vertically; views have direct sidebar access. Not a complete assistive-technology/high-DPI certification.
* Dark/light screenshots and preference persistence checked in browser. Actual visual state is represented by the saved captures, not generated concept art.

## Material findings and limits

A newly created second loopMIDI cable accepted sends without delivering data until loopMIDI was restarted and handles reopened. The first smoke run subsequently failed with500 on a cached pre-restart output handle. Explicitly reopening that destination resolved it; the passing script contains that setup step. Preserve this finding in release notes/test work. Automatic recovery after driver restart remains a release qualification item.

The Studio UI and backend are a working development revision, not a Windows setup package or a certification of stage readiness. No physical MIDI interface/pedal/instrument qualification was performed, no installer was built or tested, and no long-duration physical timing measurement was performed. The short clock sample measures Windows callback arrival. Existing broader audit concerns need current-source release review.

The integrated keybed presently sends notes/velocity; extra controls such as sustain remain available in the separate desktop keyboard. Pedal mappings are explicitly demonstration mappings. Its footswitch is a received-state indicator. There is no audio engine or decorative audio waveform. Received-state indicators reset when explicitly reconnecting the receiver.

## Reproduce

Run `python tests/run_tests.py` in an isolated checkout/config environment. Run the supplied studio_smoke.py against the development preview on127.0.0.1:18795 with only the named loopMIDI ports. The script is deliberately not a physical-device test. Do not point it at an unrelated live server.

The ordinary launcher remains run_app.py / run_app.bat on8765. The application must restart after Python backend changes. Preview configuration and its temporary action are separate from user_config.json.

Before copying source, hashes of all four existing replacement files were compared with their inspection snapshots and matched. Original files are preserved in the project's DesignBackups folder. No user config or separate desktop instrument source was replaced by this UI deployment.

## Research

* [Ableton routing and I/O](https://www.ableton.com/en/manual/routing-and-i-o/): separate MIDI input/output roles.
* [Kontakt Classic View](https://docs.native-instruments.com/ni-tech-manuals/kontakt-manual/en/classic-view): focused rack, displays and on-screen-keyboard organization.
* [Steinberg input/output monitor](https://www.steinberg.help/r/cubase-artist/15.0/en/cubase_nuendo/topics/setting_up/input_monitor_r.html): directional diagnostics.
* [MIDI-OX](https://www.midiox.com/app.htm): independent diagnostic reference, not a runtime dependency.
* User-supplied Sound On Sound article: full page returned403; indexed material was available. No claim of a complete article reading or copied visual assets.

## Installed-app confirmation

The redesigned source was installed into D:\Projects\MIDI after backups were created. The idle normal engine was restarted on127.0.0.1:8765. Browser interactions confirmed PC24 at the reference receiver, a middle-C press/release in the main RX monitor, and a rotary value change64→65 producing received CC11/value65. Both installed themes were captured. Dark theme persisted after a page reload; no horizontal overflow was observed at the normal browser width. The UI was left open on the standard application address. The original user configuration file was not replaced by preview configuration.
