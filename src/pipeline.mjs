import fs from 'node:fs/promises';
import path from 'node:path';
import { getProvider } from './providers.mjs';

export async function buildPlan(inputFile) {
  const raw = await fs.readFile(inputFile, 'utf8');
  const idea = JSON.parse(raw);
  const provider = getProvider(idea.providers?.story || process.env.STORY_PROVIDER || 'mock');
  const project = await provider.story(idea);
  const scenes = (project.scenes || []).map((scene, i) => ({ ...scene, id: scene.id || `s${i + 1}`, imagePrompt: scene.imagePrompt || scene.visual || '', dialogue: scene.dialogue || scene.lines || [] }));
  return { ...project, scenes, format: 'vertical', width: 1080, height: 1920, fps: 30 };
}

export async function prepareAssets(plan, outDir) {
  await fs.mkdir(outDir, { recursive: true });
  const imageProvider = getProvider(process.env.MEDIA_PROVIDER || 'real');
  const voiceProvider = imageProvider;
  const assets = [];
  for (const scene of plan.scenes) {
    const image = await imageProvider.image(scene);
    let imagePath = null;
    if (image.buffer) { imagePath = path.join(outDir, `${scene.id}.png`); await fs.writeFile(imagePath, image.buffer); }
    const voices = [];
    for (let i = 0; i < (scene.dialogue || []).length; i++) {
      const line = scene.dialogue[i];
      const voiceName = line.voice || line.speaker || 'narrator';
      const voice = await voiceProvider.voice(line, voiceName);
      let audioPath = null;
      if (voice.audioBuffer) { audioPath = path.join(outDir, `${scene.id}-${i + 1}.mp3`); await fs.writeFile(audioPath, voice.audioBuffer); }
      voices.push({ ...voice, audioPath });
    }
    assets.push({ sceneId: scene.id, duration: scene.duration, imagePath, voices });
  }
  await fs.writeFile(path.join(outDir, 'assets.json'), JSON.stringify(assets, null, 2));
  return assets;
}
