import fs from 'node:fs/promises';
import path from 'node:path';
import { getProvider } from './providers.mjs';
import { validateProject } from './schema.mjs';

const CHARACTER_VOICES = [
  { female: 'en-US-AriaNeural', male: 'en-US-GuyNeural' },
  { female: 'en-US-JennyNeural', male: 'en-US-DavisNeural' },
  { female: 'en-US-SaraNeural', male: 'en-US-JasonNeural' },
  { female: 'en-US-MichelleNeural', male: 'en-US-TonyNeural' }
];

export async function buildPlan(inputFile) {
  const raw = await fs.readFile(inputFile, 'utf8');
  const idea = JSON.parse(raw);
  const provider = getProvider(idea.providers?.story || process.env.STORY_PROVIDER || 'mock');
  const project = await provider.story(idea);
  validateProject(project);

  const characters = Array.isArray(project.characters) ? project.characters : [];
  const characterMap = new Map();

  characters.forEach((character, index) => {
    const gender = String(character.gender || '').toLowerCase() === 'male' ? 'male' : 'female';
    const voices = CHARACTER_VOICES[index % CHARACTER_VOICES.length];
    characterMap.set(String(character.name).toLowerCase(), {
      ...character,
      voice: voices[gender],
      characterId: `character-${index + 1}`
    });
  });

  const characterBible = characters.map((character) => {
    const mapped = characterMap.get(String(character.name).toLowerCase());
    return `${mapped.name}: ${mapped.gender}; ${mapped.appearance}; voice=${mapped.voice}`;
  }).join('\n');

  const scenes = (project.scenes || []).map((scene, i) => {
    const dialogue = (scene.dialogue || scene.lines || []).map((line) => {
      const character = characterMap.get(String(line.speaker || '').toLowerCase());
      return { ...line, voice: character?.voice || line.voice || CHARACTER_VOICES[0].female };
    });
    const speakers = [...new Set(dialogue.map((line) => String(line.speaker || '').toLowerCase()))]
      .map((name) => characterMap.get(name)).filter(Boolean);
    const sceneCharacters = speakers.length ? speakers : characters.map((c) => characterMap.get(String(c.name).toLowerCase())).filter(Boolean);
    const continuity = sceneCharacters.map((character) => `${character.name}: ${character.appearance}`).join('; ');
    const imagePrompt = `${scene.imagePrompt || scene.visual || ''}. CHARACTER CONTINUITY: ${continuity}. Keep each named character exactly the same person, gender, face, hair, skin tone, clothing identity and distinctive features. Do not introduce replacement people. Cinematic vertical composition, detailed lighting, 9:16.`;
    return { ...scene, id: scene.id || `s${i + 1}`, imagePrompt, dialogue, characterIds: sceneCharacters.map((c) => c.characterId) };
  });

  return { ...project, characters, characterBible, scenes, format: 'vertical', width: 1080, height: 1920, fps: 30 };
}

export async function prepareAssets(plan, outDir) {
  await fs.mkdir(outDir, { recursive: true });
  const mediaProvider = getProvider(process.env.MEDIA_PROVIDER || 'real');
  const referencesDir = path.join(outDir, 'characters');
  await fs.mkdir(referencesDir, { recursive: true });

  let referenceBuffer = null;
  if (plan.characters?.length && typeof mediaProvider.characterReference === 'function') {
    const reference = await mediaProvider.characterReference(plan.characters);
    if (reference?.buffer) {
      referenceBuffer = reference.buffer;
      await fs.writeFile(path.join(referencesDir, 'reference-sheet.png'), referenceBuffer);
    }
  }

  const assets = [];
  for (const scene of plan.scenes) {
    const image = await mediaProvider.image({ ...scene, referenceBuffer });
    let imagePath = null;
    if (image.buffer) {
      imagePath = path.join(outDir, `${scene.id}.png`);
      await fs.writeFile(imagePath, image.buffer);
    }
    if (!imagePath) throw new Error(`Image provider returned no image for ${scene.id}`);

    const voices = [];
    for (let i = 0; i < (scene.dialogue || []).length; i++) {
      const line = scene.dialogue[i];
      const voice = await mediaProvider.voice(line, line.voice || line.speaker || 'narrator');
      let audioPath = null;
      if (voice.audioBuffer) {
        audioPath = path.join(outDir, `${scene.id}-${i + 1}.mp3`);
        await fs.writeFile(audioPath, voice.audioBuffer);
      }
      if (scene.dialogue.length && !audioPath) throw new Error(`Voice provider returned no audio for ${scene.id} dialogue ${i + 1}`);
      voices.push({ ...voice, audioPath });
    }
    assets.push({ sceneId: scene.id, duration: scene.duration, imagePath, voices, characterIds: scene.characterIds || [] });
  }
  await fs.writeFile(path.join(outDir, 'assets.json'), JSON.stringify(assets, null, 2));
  return assets;
}
