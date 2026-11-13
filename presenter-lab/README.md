# Presenter Lab (isolated preview)

This is a separate experiment from EDUFORGE StickLab. It does not replace or edit StickLab.

## Add the supplied character

Upload the supplied character as `Presenter.glb` to:

`presenter-lab/assets/Presenter.glb`

The binary model is intentionally kept separate from the scripts. Once it is present, run **Presenter Lab Preview** from the Actions tab (or push a change under `presenter-lab/**`).

## What this first test does

- Imports the GLB into Blender.
- Finds the visible mesh and calculates its bounds.
- Creates a simple studio floor, camera and lights.
- Renders a six-second turntable preview MP4.
- Uploads the MP4 and a model-inspection report as workflow artifacts.

## Current model capability notes

The uploaded GLB was inspected before this workflow was prepared:
- One skinned mesh and one humanoid armature with 53 bones.
- No embedded animation clips.
- No facial morph targets / shape keys were present in the GLB.

The lab now includes a rig-driven body-motion test (breathing, head movement and presentation gestures). Facial geometry, blinking, expressions and lip-sync are separate work because the supplied model has no facial shape keys. The original GLB is kept unchanged.
