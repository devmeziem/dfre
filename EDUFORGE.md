# Project notes

## Current test

**How a Solar Eclipse Happens** — a 15-second, 720 × 1280 animation at 24 FPS.

The scene is generated procedurally in Blender from `seeds/solar_eclipse.json`. It includes the Sun, Earth, Moon, orbit path, shadow cone, lighting, camera movement, labels, and timed callouts.

The GitHub Actions workflow then:
1. Validates the seed file.
2. Renders the silent scene with Blender.
3. Generates narration and timed SRT captions using Edge TTS.
4. Combines video, audio, and burned-in captions with FFmpeg.
5. Checks the final MP4 and uploads it as an artifact.

## Run

Go to **Actions → Render short → Run workflow** and choose a seed JSON file. The default is `seeds/solar_eclipse.json`.

The output artifact is named `eduforge-short` and is retained for seven days.

## Scope

This is an early procedural-rendering pipeline. It uses no external 3D assets or paid AI API. Review scientific content and rendered output before publishing.
