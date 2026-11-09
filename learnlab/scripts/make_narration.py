#!/usr/bin/env python3
"""Build narration and captions for a LearnLab lesson using Edge TTS."""
import json
import pathlib
import subprocess
import sys
import tempfile
import wave


def run(args):
    subprocess.run(args, check=True)


def stamp(seconds):
    millis = round(seconds * 1000)
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    whole, millis = divmod(millis, 1000)
    return f"{hours:02}:{minutes:02}:{whole:02},{millis:03}"


def wrap_caption(text, width=40):
    words = text.split()
    lines, current = [], ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) > width and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    # At most two subtitle lines per cue; keep each seed beat concise.
    if len(lines) > 2:
        raise ValueError(f"Narration beat is too long for one caption cue: {text}")
    return "\n".join(lines)


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: make_narration.py SEED_JSON OUTPUT_DIR")
    seed_path = pathlib.Path(sys.argv[1]).resolve()
    repo_root = pathlib.Path.cwd().resolve()
    seeds_root = (repo_root / "learnlab" / "seeds").resolve()
    if seeds_root not in seed_path.parents:
        raise SystemExit("Seed must be inside learnlab/seeds")
    out_dir = pathlib.Path(sys.argv[2]).resolve()
    if repo_root not in out_dir.parents:
        raise SystemExit("Output directory must be inside the repository workspace")
    data = json.loads(seed_path.read_text(encoding="utf-8"))
    project = data.get("project", {})
    lesson = data.get("lesson", {})
    beats = lesson.get("narration_beats", [])
    if not beats or not lesson.get("source_url") or not lesson.get("learning_goal"):
        raise SystemExit("Seed needs a learning goal, source URL, and narration beats")
    voice = project.get("voice", "en-US-AriaNeural")
    rate = project.get("voice_rate", "-5%")
    out_dir.mkdir(parents=True, exist_ok=True)
    wav_path = out_dir / "narration.wav"
    srt_path = out_dir / "captions.srt"
    duration_path = out_dir / "duration.json"
    params = None
    caption_blocks = []
    cursor = 0.0
    pause_seconds = 0.22
    pause_frames = None

    with tempfile.TemporaryDirectory(prefix="learnlab-tts-") as temp_dir:
        temp = pathlib.Path(temp_dir)
        wavs = []
        for index, beat in enumerate(beats, 1):
            text = str(beat.get("text", "")).strip()
            if not text:
                raise SystemExit(f"Narration beat {index} is empty")
            mp3 = temp / f"beat-{index:02}.mp3"
            wav = temp / f"beat-{index:02}.wav"
            run([
                sys.executable, "-m", "edge_tts",
                "--voice", voice, f"--rate={rate}", "--text", text,
                "--write-media", str(mp3),
            ])
            run([
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-i", str(mp3), "-ar", "24000", "-ac", "1",
                "-c:a", "pcm_s16le", str(wav),
            ])
            wavs.append((wav, text))

        with wave.open(str(wav_path), "wb") as output:
            for index, (wav, text) in enumerate(wavs):
                with wave.open(str(wav), "rb") as source:
                    current = source.getparams()
                    if params is None:
                        params = current
                        output.setparams(params)
                        pause_frames = round(pause_seconds * params.framerate)
                    elif (current.nchannels, current.sampwidth, current.framerate, current.comptype) != (params.nchannels, params.sampwidth, params.framerate, params.comptype):
                        raise SystemExit("TTS beat audio formats differ")
                    frames = source.readframes(source.getnframes())
                    beat_duration = len(frames) / (params.nchannels * params.sampwidth * params.framerate)
                    start = cursor
                    output.writeframesraw(frames)
                    cursor += beat_duration
                    caption_blocks.append((index + 1, start, cursor, wrap_caption(text)))
                    if index != len(wavs) - 1:
                        output.writeframesraw(b"\0" * pause_frames * params.nchannels * params.sampwidth)
                        cursor += pause_frames / params.framerate
            output.writeframes(b"")

    with srt_path.open("w", encoding="utf-8") as srt:
        for index, start, end, text in caption_blocks:
            srt.write(f"{index}\n{stamp(start)} --> {stamp(end)}\n{text}\n\n")
    duration_path.write_text(json.dumps({"duration_seconds": round(cursor, 3)}, indent=2) + "\n", encoding="utf-8")
    print(f"Narration: {cursor:.2f}s across {len(beats)} beats; captions written to {srt_path}")


if __name__ == "__main__":
    main()
