#!/usr/bin/env python3
"""Fail the workflow when the rendered lesson is incomplete or malformed."""
import json
import pathlib
import subprocess
import sys

if len(sys.argv) != 3:
    raise SystemExit("usage: validate_output.py VIDEO SEED_JSON")
video = pathlib.Path(sys.argv[1])
seed_path = pathlib.Path(sys.argv[2])
if not video.is_file() or video.stat().st_size < 20_000:
    raise SystemExit("Final MP4 is missing or unexpectedly small")
seed = json.loads(seed_path.read_text(encoding="utf-8"))
lesson = seed.get("lesson", {})
if not lesson.get("learning_goal") or not lesson.get("source_url", "").startswith("https://"):
    raise SystemExit("Seed must contain a learning goal and HTTPS source URL")
probe = subprocess.check_output([
    "ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(video)
], text=True)
meta = json.loads(probe)
streams = meta.get("streams", [])
video_streams = [stream for stream in streams if stream.get("codec_type") == "video"]
audio_streams = [stream for stream in streams if stream.get("codec_type") == "audio"]
if len(video_streams) != 1 or len(audio_streams) != 1:
    raise SystemExit("Expected exactly one video stream and one narration audio stream")
video_stream = video_streams[0]
project = seed["project"]
expected = (int(project.get("width", 720)), int(project.get("height", 1280)))
actual = (int(video_stream.get("width", 0)), int(video_stream.get("height", 0)))
if actual != expected or actual[1] <= actual[0]:
    raise SystemExit(f"Unexpected video dimensions: got {actual}, expected portrait {expected}")
duration = float(meta["format"].get("duration", 0))
if not 5 <= duration <= 180:
    raise SystemExit(f"Video duration out of allowed range: {duration:.2f}s")
if video_stream.get("codec_name") != "h264" or audio_streams[0].get("codec_name") != "aac":
    raise SystemExit("Expected H.264 video and AAC audio")
print(json.dumps({"video": str(video), "bytes": video.stat().st_size, "dimensions": actual, "duration_seconds": round(duration, 2), "video_codec": "h264", "audio_codec": "aac"}, indent=2))
