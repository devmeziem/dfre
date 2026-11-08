# EDUFORGE

A small procedural animation test project.

## Run

Open **Actions → Render short → Run workflow**. The default input is `seeds/solar_eclipse.json`.

The workflow renders a vertical 3D scene with Blender, generates narration and timed captions with Edge TTS, combines the media with FFmpeg, validates the MP4, and uploads the result as a workflow artifact.

## Local requirements

- Blender with the Eevee renderer
- Python 3
- Edge TTS (`python -m pip install edge-tts`)
- FFmpeg with subtitle support

## Files

- `blender/render_short.py` — procedural scene and animation
- `scripts/make_narration.py` — narration and subtitle generation
- `seeds/` — scene input data

Generated files are written to `output/` and are not committed.
