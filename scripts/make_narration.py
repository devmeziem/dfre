import json, pathlib, subprocess, sys, re, wave, contextlib

seed_path=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "seeds/solar_eclipse.json")
out_dir=pathlib.Path(sys.argv[2] if len(sys.argv)>2 else "output")
out_dir.mkdir(parents=True,exist_ok=True)
data=json.loads(seed_path.read_text(encoding="utf-8"))
beats=data["scene"].get("narration_beats",[])
text=" ".join(b["text"].strip() for b in beats if b.get("text","").strip())
if not text: raise SystemExit("No narration beats found")
audio=out_dir/"narration.mp3"; raw_srt=out_dir/"edge-captions.srt"; subs=out_dir/"captions.srt"
voice=data["project"].get("voice","en-US-AriaNeural"); rate=data["project"].get("voice_rate","-5%")
subprocess.run([sys.executable,"-m","edge_tts","--voice",voice,f"--rate={rate}","--text",text,"--write-media",str(audio),"--write-subtitles",str(raw_srt)],check=True)
# Convert long sentence captions into short, readable 3-5 word beats.
probe=subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","default=nw=1:nk=1",str(audio)],text=True).strip()
duration=float(probe)
words=re.findall(r"\S+",text)
weights=[max(1,len(re.sub(r"[^A-Za-z0-9]","",w))) for w in words]
total=sum(weights); cursor=0.0; idx=1; lines=[]
while idx<=len(words):
    chunk=words[idx-1:idx+4]
    wsum=sum(weights[idx-1:idx+4])
    start=cursor
    span=duration*wsum/total
    end=min(duration,start+span)
    def stamp(v):
        ms=int(round(v*1000)); h=ms//3600000; ms%=3600000; m=ms//60000; ms%=60000; s=ms//1000; ms%=1000
        return f"{h:02}:{m:02}:{s:02},{ms:03}"
    lines += [str(len(lines)+1),f"{stamp(start)} --> {stamp(end)}"," ".join(chunk),""]; cursor=end; idx+=5
subs.write_text("\n".join(lines),encoding="utf-8")
print(f"Generated narration ({duration:.2f}s) and {len(lines)//4} short caption beats.",flush=True)
