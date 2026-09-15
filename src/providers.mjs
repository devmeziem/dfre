import { generateStory } from './providers/story.mjs';
import { generateImage, generateCharacterReference } from './providers/image.mjs';
import { generateVoice } from './providers/voice.mjs';

export function getProvider(name = 'mock', env = process.env) {
  if (name === 'mock') return new MockProvider();
  if (name === 'real' || name === 'cloudflare') return new RealProvider(env);
  throw new Error(`Unknown provider: ${name}`);
}

export class MockProvider {
  async story(idea) {
    return {
      title: idea.title || 'Untitled',
      genre: idea.genre || 'mystery',
      durationSeconds: idea.durationSeconds || 45,
      characters: idea.characters || [],
      scenes: [{ id: 's1', duration: 5, location: 'interior', imagePrompt: idea.visual || 'cinematic scene', dialogue: [] }]
    };
  }
  async image(prompt) { return { type: 'image', prompt, path: null }; }
  async characterReference(characters, environment) { return generateCharacterReference(characters, environment, process.env); }
  async voice(text, voice) { return { type: 'audio', text, voice, path: null }; }
}

export class RealProvider {
  constructor(env = process.env) { this.env = env; }
  async story(input) { return generateStory(input, this.env); }
  async image(scene) { return generateImage(scene, this.env); }
  async characterReference(characters, environment) { return generateCharacterReference(characters, environment, this.env); }
  async voice(line, voice) { return generateVoice(line, voice, this.env); }
}
