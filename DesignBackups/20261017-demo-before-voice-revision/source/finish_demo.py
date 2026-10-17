from pathlib import Path
import json,re,html,subprocess
import imageio_ffmpeg
R=Path(__file__).resolve().parent
data=json.loads((R/'chapters.json').read_text())
def stamp(t):
 ms=round(t*1000);return f'{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d},{ms%1000:03d}'
def mm(t):return f'{int(t)//60:02d}:{int(t)%60:02d}'
subs=[]
for c in data['chapters']:
 words=c['narration'].split();chunks=[];line=[]
 for w in words:
  line.append(w)
  if len(' '.join(line))>66:chunks.append(' '.join(line));line=[]
 if line:chunks.append(' '.join(line))
 total=sum(len(x.split()) for x in chunks);cur=c['start']+.3
 span=c['end']-c['start']-1.2
 for ch in chunks:
  end=cur+span*len(ch.split())/total
  subs.append(f'{len(subs)+1}\n{stamp(cur)} --> {stamp(end)}\n{ch}')
  cur=end
(R/'RITYM-PulseStage-Guided-Demo.srt').write_text('\n\n'.join(subs)+'\n',encoding='utf-8')
vtt='WEBVTT\n\n'+'\n\n'.join(re.sub(r'(?<=\d),(?=\d{3})','.',s) for s in subs)+'\n'
(R/'captions.vtt').write_text(vtt,encoding='utf-8')
chapters='\n'.join(f'- **{mm(c["start"])} — {c["title"]}**' for c in data['chapters'])
guide=f'''# RITYM PulseStage — Guided Demo

Duration: {mm(data['duration_seconds'])}. Full HD 1920 × 1080, 24 fps, English synthetic narration, on-screen explanations and optional subtitle files.

Open **Watch-Demo.html** or **RITYM-PulseStage-Guided-Demo.mp4**. Enable CC in the HTML player for subtitles. The SRT is available for desktop players.

This is an edited walkthrough using verified still captures of the actual application, with narration and close-ups. It is not a continuous screen recording. It demonstrates local virtual MIDI delivery; it does not claim physical hardware or audio testing.

## Chapters

{chapters}

## Repeat the demonstration

1. Start loopMIDI. Ensure both **PulseStage Keyboard** and **PulseStage Pedal Test** ports exist. Start PulseStage and select the Control room.
2. Choose **Input: PulseStage Keyboard** and **Output: PulseStage Pedal Test**. Use **Connect receiver** if required. The keybed sends to the Keyboard port; the reference receiver listens on Pedal Test. No automatic MIDI thru connects these paths.
3. Click and release C4 on the integrated keyboard. Open Event monitor and confirm received Note On 60 and Note Off 60. Return to Control room.
4. Choose Control change, channel 1, controller **11 / Expression**. Enter **20**, click **Send command**, and confirm Expression 20 on the reference pedal. Repeat with **100**.
5. Optional: send **CC 7 = 80**, **custom CC 12 = 50**, and **custom CC 13 = 110** to reproduce the other knob positions in the video.
6. Choose **CC 64**, send **127**, and observe the illuminated ring around the metal footswitch. Send **0** to turn it off. The reference knobs and footswitch are read-only received-state indicators. CC64 is a test mapping; real hardware mappings may differ.
7. Choose Program change, enter wire value **24**, and send. The reference receiver's 1–128 display reads **025**. Check display numbering before entering a value.
8. Set clock **120 BPM**, click **Start**, and observe RUNNING plus approximately 120 BPM at the receiver. Click **Stop** after testing.

## If nothing moves

Editing a command does not transmit it: click Send command. RECEIVER ONLINE means the input handle opened; it does not prove data arrived. Check the two distinct port names, reconnect the receiver/keybed, and inspect received events. After restarting loopMIDI, refresh and reopen the ports in PulseStage. Avoid sending an output back into itself.

## MIDI-OX and real equipment

MIDI-OX is a separate MIDI message inspector. It can listen to the relevant loopMIDI port and show note, controller, program and timing messages independently. Opening a port may conflict with other applications depending on the MIDI driver; close competing handles if necessary. This demo does not show a MIDI-OX capture. The keybed has no built-in sound generator. No physical instrument is needed for this software test. Actual pedals require their own MIDI mapping and external-clock settings, and must be tested separately.

## For Antigravity

Include the video, captions and repeatable steps in offline onboarding and the updated user guide. Preserve the distinction between the keyboard input path and command output path. Label receiver knobs and the CC64 footswitch clearly as indicators to prevent users trying to turn or click them. Do not present the software test as physical hardware certification.

Source captures and reproducible rendering scripts are in the source subfolder. Narration was generated locally using the Windows Microsoft Zira voice. No music or synthesized instrument audio is included. Captions are approximately timed from narration segments, rather than word-aligned transcription.
'''
(R/'DEMO-GUIDE.md').write_text(guide,encoding='utf-8')
buttons=''.join(f'<button onclick="v.currentTime={c["start"]};v.play()"><span>{mm(c["start"])}</span>{html.escape(c["title"])}</button>' for c in data['chapters'])
(R/'Watch-Demo.html').write_text('''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>RITYM PulseStage | Guided Demo</title><style>*{box-sizing:border-box}body{background:#101516;color:#e5eadf;font:16px/1.6 'Segoe UI',sans-serif;margin:0}main{max-width:1320px;margin:auto;padding:40px}header{border-bottom:1px solid #44504a;padding-bottom:20px}h1{font-size:36px;margin:8px 0}small,button span{color:#cbaa75;letter-spacing:2px}p{color:#acbab3}video{width:100%;background:#000;border:1px solid #44504a;border-radius:8px;margin:26px 0}nav{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:10px}button{cursor:pointer;background:#202a27;border:1px solid #44504a;border-radius:6px;color:#e5eadf;padding:16px;text-align:left;font:inherit}button:hover{border-color:#cbaa75}button span{margin-right:14px}a{color:#ddbe90}footer{margin-top:30px;border-top:1px solid #44504a;padding-top:20px}</style><main><header><small>RITYM / PULSESTAGE MIDI STUDIO</small><h1>Keyboard & reference pedal</h1><p>A guided tour of two MIDI paths, received values, preset changes and clock sync.</p></header><video id="v" controls preload="metadata" poster="Poster.jpg"><source src="RITYM-PulseStage-Guided-Demo.mp4" type="video/mp4"><track src="captions.vtt" kind="captions" srclang="en" label="English"></video><nav>'''+buttons+'''</nav><footer><p>Edited walkthrough using verified application still captures and synthetic narration. Software loopback test; no physical instrument or synthesized music.</p><p><strong>Demo routing:</strong> Input = PulseStage Keyboard · Output = PulseStage Pedal Test. No automatic MIDI thru.</p><a href="DEMO-GUIDE.md">Repeat the demo / written guide</a> · <a href="RITYM-PulseStage-Guided-Demo.mp4" download>Save video</a><p>If captions are blocked when opening this local HTML file, use the adjacent SRT subtitle file in a desktop video player.</p></footer></main>''',encoding='utf-8')
from PIL import Image
Image.open(R/'scene-00.png').save(R/'Poster.jpg',quality=94)
ff=imageio_ffmpeg.get_ffmpeg_exe()
subprocess.run([ff,'-v','error','-i',str(R/'RITYM-PulseStage-Guided-Demo.mp4'),'-f','null','-'],check=True)
print('Full video/audio decode passed. Companion files ready.')
