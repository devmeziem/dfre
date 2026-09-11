import fs from 'node:fs/promises';
import path from 'node:path';
import { getProvider } from './providers.mjs';

export async function buildPlan(inputFile) {
  const raw = await fs.readFile(inputFile, 'utf8');
  const idea = JSON.parse(raw);
  const provider = getProvider(idea.providers?.story || 'mock');
  const project = await provider.story(idea);
  return { ...project, format: 'vertical', width: 1080, height: 1920 };
}

export async function prepareAssets(plan, outDir) {
  await fs.mkdir(outDir, { recursive: true });
  const provider = getProvider('mock');
  const assets = [];
  for (const scene of plan.scenes) {
    const image = await provider.image(scene.imagePrompt);
    assets.push({ sceneId: scene.id, image });
    for (const line of scene.lines || []) {
      assets.push({ sceneId: scene.id, voice: await provider.voice(line.text, line.voice || 'narrator') });
    }
  }
  await fs.writeFile(path.join(outDir, 'assets.json'), JSON.stringify(assets, null, 2));
  return assets;
}
