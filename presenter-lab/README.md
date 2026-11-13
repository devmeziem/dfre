# Presenter Lab (isolated preview)

This is a separate experiment from EDUFORGE StickLab. It does not replace or edit StickLab.

## Add the supplied character

Rename the supplied `Mike.glb` copy to `Presenter.glb`, then upload it to:

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
- One skinned mesh and one humanoid skin with 65 joints.
- No embedded animation clips.
- No facial morph targets / shape keys were present in the GLB.

This first preview deliberately tests import, framing, materials and rendering. It does not pretend the model already has facial expressions or lip-sync. Those require facial controls to be authored first.
