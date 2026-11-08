import json
import pathlib
import subprocess
import sys

seed_path = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "seeds/solar_eclipse.json")
out_dir = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else "output")
out_dir.mkdir(parents=True, exist_ok=True)

data = json.loads(seed_path.read_text(encoding="utf-8"))
beats = data["scene"].get("narration_beats", [])
text = " ".join(beat["text"].strip() for beat in beats if beat.get("text", "").strip())
if not text:
    raise SystemExit("No narration_beats found in seed JSON")

audio = out_dir / "narration.mp3"
subs = out_dir / "captions.srt"
voice = data["project"].get("voice", "en-US-AriaNeural")
rate = data["project"].get("voice_rate", "-5%")

cmd = [
    sys.executable, "-m", "edge_tts",
    "--voice", voice,
    f"--rate={rate}",
    "--text", text,
    "--write-media", str(audio),
    "--write-subtitles", str(subs),
]
print("Generating narration with", voice, "at", rate, flush=True)
subprocess.run(cmd, check=True)
if not audio.is_file() or audio.stat().st_size < 1000:
    raise SystemExit("Edge TTS did not produce a valid audio file")
if not subs.is_file() or subs.stat().st_size == 0:
    raise SystemExit("Edge TTS did not produce subtitle captions")
print("Narration and timed captions generated:", audio, subs, flush=True)
