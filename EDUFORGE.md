# EDUFORGE procedural 3D test

First Blender-only proof of concept for EDUFORGE, added alongside the existing dfre pipeline.

## Test topic
**How a Solar Eclipse Happens** — a 15-second vertical educational animation.

## What this test checks
- Blender builds a scene from a JSON seed without external 3D assets.
- The scene includes a Sun, Earth, Moon, orbit guide, shadow cone, lighting, camera movement and labels.
- The Moon animates into alignment to demonstrate the eclipse concept.
- GitHub Actions installs Blender and FFmpeg, renders in background mode, validates the MP4 and uploads it as a seven-day artifact.

## Run
Open **Actions → EDUFORGE - Procedural 3D Short Test → Run workflow**.
The workflow defaults to `seeds/solar_eclipse.json`.

## Output
Artifact: `eduforge-procedural-3d-short`.

The initial render is 720 × 1280 at 24 FPS to keep the first CI test manageable. If render time and visual quality are acceptable, raise it to 1080 × 1920 / 30 FPS.

## Scope
This is a visual proof of concept, not the full automated production pipeline. It does not yet generate narration, captions, source cards or YouTube metadata. No external 3D generation service or API key is used.
