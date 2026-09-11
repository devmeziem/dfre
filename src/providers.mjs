export function getProvider(name, env = process.env) {
  if (name === 'mock') return new MockProvider();
  throw new Error(`Unknown provider: ${name}`);
}

export class MockProvider {
  async story(idea) {
    return {
      title: idea.title || 'Untitled',
      scenes: [
        { id: 's1', duration: 5, location: 'interior', imagePrompt: idea.visual || 'cinematic scene', lines: [] }
      ]
    };
  }
  async image(prompt) { return { type: 'image', prompt, path: null }; }
  async voice(text, voice) { return { type: 'audio', text, voice, path: null }; }
}
