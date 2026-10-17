"""Render the PulseStage product walkthrough from real UI captures and narration."""
from pathlib import Path
import json,math,re,html,subprocess,wave
from PIL import Image,ImageDraw,ImageFont,ImageOps
import imageio_ffmpeg
R=Path(__file__).resolve().parent
PLAN=json.loads((R/'demo-plan.json').read_text(encoding='utf-8'))
FF=imageio_ffmpeg.get_ffmpeg_exe()
def font(n,b=False):return ImageFont.truetype('C:/Windows/Fonts/'+('segoeuib.ttf' if b else 'segoeui.ttf'),n)
def text(d,s,xy,n=28,width=500,color='#dfe6df',bold=False):
 x,y=xy;f=font(n,bold)
 for par in s.split('\n'):
  line=''
  for word in par.split():
   trial=(line+' '+word).strip()
   if d.textlength(trial,font=f)>width and line:d.text((x,y),line,font=f,fill=color);y+=n+12;line=word
   else:line=trial
  d.text((x,y),line,font=f,fill=color);y+=n+12
 return y
def scene(i,p,suffix=''):
 im=Image.new('RGB',(1920,1080),'#13191a');d=ImageDraw.Draw(im)
 d.text((64,36),'PulseStage',font=font(36,True),fill='#dec69e')
 d.text((290,48),'MIDI STUDIO',font=font(20),fill='#94a59c')
 d.text((1515,48),f'WALKTHROUGH  /  {i+1:02d}',font=font(19),fill='#94a59c')
 d.line((64,108,1856,108),fill='#39463e',width=2)
 text(d,p['title'],(64,145),46,1780,'#f1f0e8',True)
 d.rounded_rectangle((64,250,1300,940),radius=10,fill='#1b2424',outline='#45544a',width=2)
 if i in (0,1,11):
  if i==0:
   text(d,'The connection is easy.\nKnowing it worked is the challenge.',(112,310),40,1080,'#eff0e5',True)
   for j,(a,b) in enumerate([('SEND','Did the instruction leave the computer?'),('RECEIVE','Did it reach the intended device?'),('RESPOND','Did the device do what we expected?')]):
    yy=485+j*125;d.rounded_rectangle((112,yy,1252,yy+100),radius=8,fill='#26332d');d.text((140,yy+29),a,font=font(25,True),fill='#dec69e');text(d,b,(340,yy+30),26,850)
  elif i==1:
   text(d,'A safe place to check the messages.',(112,315),40,1080,'#eff0e5',True)
   for j,(a,b) in enumerate([('Keyboard','Play a note -> inspect the received event'),('Command station','Send a setting -> observe the reference pedal'),('Real equipment','Use its documented MIDI settings -> verify its response')]):
    yy=445+j*140;d.rounded_rectangle((112,yy,1252,yy+115),radius=8,fill='#26332d');d.text((140,yy+16),a,font=font(27,True),fill='#dec69e');text(d,b,(140,yy+59),24,1070)
  else:
   text(d,'What is included — and what is separate',(112,290),36,1090,'#eff0e5',True)
   rows=[('Inside PulseStage','Keybed + reference receiver + MIDI controls'),('Virtual test connection','loopMIDI: separate installation, kept running'),('Independent checking','MIDI-OX: optional, not required'),('Developer version today','Python + application packages + browser'),('Final Windows setup','Must bundle runtime and packages; not built yet')]
   for j,(a,b) in enumerate(rows):
    yy=390+j*100;d.line((112,yy-10,1252,yy-10),fill='#3c4b42');text(d,a,(112,yy),23,350,'#dec69e',True);text(d,b,(490,yy),23,755)
 else:
  src=Image.open(R/p['image']).convert('RGB')
  crop=p['crop']
  if i==4:crop=[200,540,1005,750]
  if crop:src=src.crop(crop)
  fit=ImageOps.contain(src,(1208,662),Image.Resampling.LANCZOS)
  im.paste(fit,(64+(1236-fit.width)//2,250+(690-fit.height)//2))
 yy=text(d,p['caption'],(1350,300),31,490,'#e6ece4',True)
 d.line((1350,yy+30,1840,yy+30),fill='#46564a',width=2)
 text(d,p['note'],(1350,yy+60),24,490,'#a8b8ac')
 d.text((64,985),'CONTROL  /  OBSERVE  /  VERIFY',font=font(18),fill='#9aaea0')
 d.text((1350,985),'A PRACTICAL MIDI WALKTHROUGH',font=font(18),fill='#c6af87')
 d.rectangle((64,1035,1856,1040),fill='#303d34');d.rectangle((64,1035,64+int(1792*(i+1)/len(PLAN)),1040),fill='#c6af87')
 im.save(R/f'scene-{i:02d}{suffix}.png')
def run(args):subprocess.run([FF,'-y','-v','error']+args,check=True)
def stamp(t):
 ms=round(t*1000);return f'{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d},{ms%1000:03d}'
def mm(t):return f'{int(t)//60:02d}:{int(t)%60:02d}'
timeline=[];total=0;clips=[]
for i,p in enumerate(PLAN):
 scene(i,p)
 run(['-i',str(R/f'voice-{i:02d}.mp3'),'-af','loudnorm=I=-16:TP=-1.5:LRA=7','-ac','1','-ar','48000',str(R/f'voice-{i:02d}.wav')])
 with wave.open(str(R/f'voice-{i:02d}.wav')) as w:duration=math.ceil((w.getnframes()/w.getframerate()+1)*24)/24
 target=R/f'clip-{i:02d}.mp4'
 frames=[(R/f'scene-{i:02d}.png',duration)]
 if i==6:
  scene(i,dict(p,image='expression-low.jpg'),'-before')
  frames=[(R/f'scene-{i:02d}-before.png',6),(R/f'scene-{i:02d}.png',duration-6)]
 elif i==7:
  scene(i,dict(p,image='control.jpg'),'-after')
  frames=[(R/f'scene-{i:02d}.png',duration-5),(R/f'scene-{i:02d}-after.png',5)]
 elif i==9:
  scene(i,dict(p,image='program.jpg'),'-before');scene(i,dict(p,image='control.jpg'),'-after')
  frames=[(R/f'scene-{i:02d}-before.png',5),(R/f'scene-{i:02d}.png',duration-10),(R/f'scene-{i:02d}-after.png',5)]
 visual_list=R/f'visuals-{i:02d}.txt'
 visual_list.write_text(''.join("file '"+f.as_posix()+"'\nduration "+str(seconds)+"\n" for f,seconds in frames)+"file '"+frames[-1][0].as_posix()+"'\n",encoding='utf-8')
 run(['-f','concat','-safe','0','-i',str(visual_list),'-i',str(R/f'voice-{i:02d}.wav'),'-vf',f'fps=24,fade=t=in:st=0:d=0.3,fade=t=out:st={duration-.3}:d=0.3','-af','apad','-t',str(duration),'-c:v','libx264','-preset','fast','-tune','stillimage','-crf','19','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-ar','48000',str(target)])
 timeline.append(dict(p,start=total,end=total+duration));total+=duration;clips.append(target)
 print(f'Rendered chapter {i+1}/{len(PLAN)}',flush=True)
(R/'concat.txt').write_text(''.join("file '"+x.as_posix()+"'\n" for x in clips),encoding='utf-8')
run(['-f','concat','-safe','0','-i',str(R/'concat.txt'),'-c','copy','-movflags','+faststart',str(R/'PulseStage-Guided-Demo.mp4')])
subs=[]
for c in timeline:
 words=c['narration'].split();chunks=[];line=[]
 for w in words:
  if len(' '.join(line+[w]))>70 and line:chunks.append(' '.join(line));line=[]
  line.append(w)
 if line:chunks.append(' '.join(line))
 count=sum(len(x.split()) for x in chunks);cur=c['start']+.2;span=c['end']-c['start']-1
 for ch in chunks:
  end=cur+span*len(ch.split())/count;subs.append(f'{len(subs)+1}\n{stamp(cur)} --> {stamp(end)}\n{ch}');cur=end
(R/'PulseStage-Guided-Demo.srt').write_text('\n\n'.join(subs)+'\n',encoding='utf-8')
(R/'captions.vtt').write_text('WEBVTT\n\n'+'\n\n'.join(re.sub(r'(?<=\d),(?=\d{3})','.',s) for s in subs)+'\n',encoding='utf-8')
(R/'chapters.json').write_text(json.dumps({'duration_seconds':total,'voice':'Benjamin, American male preset; speed 0.83; synthetic narration','format':'Edited walkthrough using verified application still captures and explanatory graphics, not a continuous screen recording','chapters':timeline},indent=2),encoding='utf-8')
Image.open(R/'scene-00.png').save(R/'Poster.jpg',quality=94)
buttons=''.join(f'<button onclick="v.currentTime={c["start"]};v.play()"><span>{mm(c["start"])}</span>{html.escape(c["title"])}</button>' for c in timeline)
(R/'Watch-Demo.html').write_text('''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>PulseStage | Guided Demo</title><style>*{box-sizing:border-box}body{background:#13191a;color:#e5eadf;font:16px/1.6 'Segoe UI',sans-serif;margin:0}main{max-width:1320px;margin:auto;padding:40px}header{border-bottom:1px solid #44504a;padding-bottom:20px}h1{font-size:36px;margin:8px 0}small,button span{color:#cbaa75}p{color:#acbab3}video{width:100%;background:#000;border:1px solid #44504a;border-radius:8px;margin:26px 0}nav{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:10px}button{cursor:pointer;background:#202a27;border:1px solid #44504a;border-radius:6px;color:#e5eadf;padding:16px;text-align:left;font:inherit}button:hover{border-color:#cbaa75}button span{margin-right:14px}a{color:#ddbe90}footer{margin-top:30px;border-top:1px solid #44504a;padding-top:20px}</style><main><header><small>PULSESTAGE / MIDI STUDIO</small><h1>From the problem to the proof.</h1><p>A practical introduction, followed by the keyboard and reference pedal demo. American male narration, with time to follow each step.</p></header><video id="v" controls preload="metadata" poster="Poster.jpg"><source src="PulseStage-Guided-Demo.mp4" type="video/mp4"><track src="captions.vtt" kind="captions" srclang="en" label="English"></video><nav>'''+buttons+'''</nav><footer><p>Edited walkthrough with real application still captures and explanatory graphics. Synthetic narration; not a human voice recording or a continuous screen recording. Software loopback test; physical hardware response has not been verified here.</p><p><strong>Demo routing:</strong> Input = PulseStage Keyboard · Output = PulseStage Pedal Test. No automatic MIDI thru.</p><a href="DEMO-GUIDE.md">Written steps and installation requirements</a> · <a href="PulseStage-Guided-Demo.mp4" download>Save video</a><p>For desktop players, the adjacent SRT subtitle file is available. Subtitle timings are approximate.</p></footer></main>''',encoding='utf-8')
original=(R/'DEMO-GUIDE-BASE.md').read_text(encoding='utf-8')
original=re.sub(r'Duration:.*?\n','Duration: '+mm(total)+'. Full HD 1920 × 1080, 24 fps, slower American male synthetic narration.\n',original,count=1)
start=original.index('## Chapters');end=original.index('## Repeat the demonstration')
original=original[:start]+'## Chapters\n\n'+'\n'.join(f'- **{mm(c["start"])} — {c["title"]}**' for c in timeline)+'\n\n'+original[end:]
original=original.replace('Narration was generated locally using the Windows Microsoft Zira voice.','Narration uses the Benjamin American male preset, generated through Runway at 0.83 speed. It is synthetic narration, not a human recording.')
original+='''

## Physical instruments and dependencies

PulseStage lists MIDI ports exposed by Windows. A compatible powered USB-MIDI instrument, or a MIDI interface for DIN equipment, should become available for selection after Windows recognizes it. Click Refresh, then explicitly choose its input or output as appropriate. Some devices need manufacturer drivers. An audio-only instrument, audio cable, or ordinary sustain pedal is not a MIDI port. Enumeration is not proof of hardware response, and no physical hardware was verified in this demonstration.

The integrated keybed and reference receiver are part of PulseStage's interface and backend. Their current virtual test path still requires loopMIDI installed and running with both named ports. The old standalone keyboard/pedal windows are optional development utilities. MIDI-OX is optional, not a runtime requirement. Direct MIDI hardware operation does not require loopMIDI. Audible notes require a sound generator; PulseStage does not include one.

The current source-based application needs Python, FastAPI, Uvicorn, WebSockets and Pydantic plus transitive dependencies, and a browser. A completed Windows installer was not found in the source review on 17 October 2026. Antigravity must bundle Python and application packages, handle browser/WebView availability, resolve optional virtual-driver licensing and setup, and test on clean Windows. Do not claim all dependencies are already bundled.

References: [Microsoft MIDI-capable USB class driver](https://learn.microsoft.com/en-us/windows-hardware/drivers/audio/usb-2-0-audio-drivers), [loopMIDI port lifetime](https://www.tobias-erichsen.de/software/loopmidi.html).
'''
(R/'DEMO-GUIDE.md').write_text(original,encoding='utf-8')
(R/'NARRATION-TRANSCRIPT.md').write_text('# PulseStage demo narration\n\nSynthetic American male voice; deliberate pacing.\n\n'+'\n\n'.join(f'## {mm(c["start"])} — {c["title"]}\n\n{c["narration"]}' for c in timeline),encoding='utf-8')
run(['-i',str(R/'PulseStage-Guided-Demo.mp4'),'-f','null','-'])
print(f'Full decode passed. Duration {total:.2f}s. Bytes {(R/"PulseStage-Guided-Demo.mp4").stat().st_size}',flush=True)
