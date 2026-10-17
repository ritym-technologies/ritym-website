from pathlib import Path
import json, subprocess, wave, math, textwrap
from PIL import Image, ImageDraw, ImageFont, ImageOps
import imageio_ffmpeg

ROOT=Path(__file__).resolve().parent
SCENES=[
 ('Welcome to the studio','A practical tour of keyboard input and pedal control.','pedal-clock-running.jpg',None,
  'Welcome to Ritym PulseStage MIDI Studio. This guided walkthrough uses verified captures of the actual application. You can test the keyboard and reference pedal on this computer, without a physical instrument.'),
 ('Two separate signal paths','INPUT: PulseStage Keyboard\nOUTPUT: PulseStage Pedal Test','expression-high.jpg',(200,150,1005,265),
  'For this demo, choose PulseStage Keyboard as the input, and PulseStage Pedal Test as the output. The keyboard sends notes into the input monitor. The command station sends settings out to the reference pedal. There is no automatic forwarding between these paths.'),
 ('Play the virtual keyboard','Click a piano key. Release it to end the note.','pedal-clock-running.jpg',(200,790,1005,1020),
  'Click a key on the integrated piano. Pressing sends a note on message. Releasing sends note off. The keyboard has its own channel and velocity settings. This demonstrates MIDI messages; the keyboard itself does not generate audio.'),
 ('See what actually arrived','RX means received. TX means transmitted.','keyboard-monitor.jpg',None,
  'Open Event monitor to inspect incoming notes. Look for a received note on and note off pair. RX counts incoming messages, while TX counts commands sent by PulseStage. A sent message alone does not prove that the receiving device acted on it.'),
 ('Expression: start low','Control change / CC 11 / Value 20 / Send command','expression-low.jpg',(200,280,1005,680),
  'Return to Control room. Choose Control change, then controller eleven, Expression. Enter twenty and click Send command. The reference receiver shows twenty. Changing the editor alone does not send the value.'),
 ('Expression: turn it up','CC 11 changes from 20 to 100 at the receiver.','expression-high.jpg',(200,280,1005,680),
  'Now enter one hundred and send again. The receiver value and knob position change. Its four knobs show received settings: expression, volume, parameter A, and parameter B. These receiver knobs are read only indicators.'),
 ('The metal footswitch','CC 64: 127 = on / 0 = off in this test receiver.','pedal-switch-on.jpg',(640,280,1005,680),
  'The metal button below the knobs represents a footswitch. It is a read only indicator in this version. Send controller sixty four with value one hundred twenty seven to light its ring, or zero to turn it off. This is a test mapping, not a universal pedal bypass command.'),
 ('Choose a preset','Wire program 24 appears as preset 025 on the receiver.','pedal-clock-running.jpg',(200,280,1005,680),
  'Select Program change, enter twenty four, and send. The reference display reads preset twenty five because it labels presets from one to one hundred twenty eight. MIDI program values on the wire start at zero. Always check the numbering used by the target device.'),
 ('Synchronize the clock','120 BPM / Start / received RUNNING and 120.0 BPM','pedal-clock-running.jpg',(640,280,1005,680),
  'Set the master clock to one hundred twenty beats per minute and press Start. The receiver shows Running and measures approximately one hundred twenty B P M from incoming clock ticks. Press Stop when finished. Physical equipment must support external MIDI clock for this to work.'),
 ('Repeat the checks confidently','Notes received. Values received. Clock stopped when finished.','expression-high.jpg',None,
  'You have now tested keyboard input, control changes, a footswitch indicator, preset selection, and clock reception. MIDI OX can serve as a separate message inspector. These software loopback checks do not replace testing the actual musician hardware. Use the included written guide to repeat the demonstration.'),
]
def font(size,bold=False): return ImageFont.truetype('C:/Windows/Fonts/'+('segoeuib.ttf' if bold else 'segoeui.ttf'),size)
def wrap(draw,text,f,width):
 out=[]
 for p in text.split('\n'):
  line=''
  for word in p.split():
   trial=(line+' '+word).strip()
   if draw.textlength(trial,font=f)>width and line: out.append(line);line=word
   else: line=trial
  out.append(line)
 return out
def para(draw,text,xy,f,width,fill,spacing=12):
 x,y=xy
 for line in wrap(draw,text,f,width): draw.text((x,y),line,font=f,fill=fill);y+=f.size+spacing
 return y
def card(i,s):
 title,sub,file,crop,narr=s
 im=Image.new('RGB',(1920,1080),'#101516');d=ImageDraw.Draw(im)
 d.rectangle((0,0,1919,8),fill='#cbaa75')
 d.text((64,38),'RITYM',font=font(38,True),fill='#d9bd90')
 d.text((250,48),'PULSESTAGE  /  MIDI STUDIO',font=font(22),fill='#b4c0bb')
 d.text((1510,48),'GUIDED DEMONSTRATION',font=font(18),fill='#9ca9a3')
 d.line((64,110,1856,110),fill='#35403e',width=2)
 y=para(d,title,(64,145),font(48,True),1740,'#f0f0e7')
 # A fixed actual-app frame and an editorial explanation column.
 d.rounded_rectangle((64,245,1300,942),radius=18,fill='#1e2627',outline='#44504a',width=2)
 src=Image.open(ROOT/file).convert('RGB')
 if crop: src=src.crop(crop)
 fit=ImageOps.contain(src,(1204,665),Image.Resampling.LANCZOS)
 im.paste(fit,(64+(1236-fit.width)//2,245+(697-fit.height)//2))
 d.text((1350,275),f'{i+1:02d} / {len(SCENES):02d}',font=font(24),fill='#cbaa75')
 yy=para(d,sub,(1350,345),font(32,True),490,'#e5eadf',14)
 d.line((1350,yy+28,1840,yy+28),fill='#46534b',width=2)
 notes={0:'Actual application captures\nSoftware loopback demonstration',1:'Keyboard -> input monitor\nCommands -> reference receiver\nNo automatic MIDI thru',2:'Notes are MIDI data.\nA sound generator is separate.',3:'Receive evidence matters.\nInspect channel, type and bytes.',4:'Edit first. Then send.\nWatch the received value.',5:'CC 11 / CC 7 / CC 12 / CC 13\nValues range from 0 to 127.',6:'The screw-like part is the\nsimulated footswitch indicator.\nIt cannot be clicked here.',7:'0-127 wire values\n1-128 display labels',8:'24 timing ticks per quarter note\nStop the clock after testing.',9:'No physical instrument required\nfor this software test.'}
 para(d,notes[i],(1350,yy+60),font(24),490,'#aebbb4',13)
 d.text((64,982),'ACTUAL APP CAPTURES  /  NARRATED WALKTHROUGH',font=font(18),fill='#9dab9f')
 d.text((1350,982),'LOCAL MIDI TEST LAB',font=font(18),fill='#cbaa75')
 d.rectangle((64,1035,1856,1041),fill='#303a35');d.rectangle((64,1035,64+int(1792*(i+1)/len(SCENES)),1041),fill='#cbaa75')
 im.save(ROOT/f'scene-{i:02d}.png')
for i,s in enumerate(SCENES): card(i,s)
(ROOT/'narration.json').write_text(json.dumps([s[4] for s in SCENES]),encoding='utf-8')
if __name__=='__main__' and '--encode' in __import__('sys').argv:
 ff=imageio_ffmpeg.get_ffmpeg_exe(); clips=[]; timeline=[];t=0
 for i,s in enumerate(SCENES):
  audio=ROOT/f'voice-{i:02d}.wav'
  with wave.open(str(audio)) as w: duration=w.getnframes()/w.getframerate()+1.2
  duration=math.ceil(duration*24)/24
  out=ROOT/f'clip-{i:02d}.mp4'
  subprocess.run([ff,'-y','-loglevel','error','-loop','1','-framerate','24','-i',str(ROOT/f'scene-{i:02d}.png'),'-i',str(audio),'-vf',f'fade=t=in:st=0:d=0.3,fade=t=out:st={duration-.3}:d=0.3','-af','apad','-t',str(duration),'-c:v','libx264','-preset','fast','-crf','20','-tune','stillimage','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-ar','48000',str(out)],check=True)
  clips.append(out);timeline.append({'start':t,'end':t+duration,'title':s[0],'narration':s[4],'caption':s[1]});t+=duration
  print(f'Encoded chapter {i+1}/{len(SCENES)}',flush=True)
 (ROOT/'concat.txt').write_text(''.join("file '"+p.as_posix()+"'\n" for p in clips),encoding='utf-8')
 target=ROOT/'RITYM-PulseStage-Guided-Demo.mp4'
 subprocess.run([ff,'-y','-loglevel','error','-f','concat','-safe','0','-i',str(ROOT/'concat.txt'),'-c','copy','-movflags','+faststart',str(target)],check=True)
 def stamp(t):
  ms=round(t*1000);return f'{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d},{ms%1000:03d}'
 (ROOT/'RITYM-PulseStage-Guided-Demo.srt').write_text('\n\n'.join(f'{i+1}\n{stamp(c["start"])} --> {stamp(c["end"])}\n{c["narration"]}' for i,c in enumerate(timeline))+'\n',encoding='utf-8')
 (ROOT/'chapters.json').write_text(json.dumps({'duration_seconds':t,'type':'Narrated walkthrough using verified application still captures, not a continuous recording','chapters':timeline},indent=2),encoding='utf-8')
 print(f'Duration: {t:.2f} seconds; bytes: {target.stat().st_size}',flush=True)
