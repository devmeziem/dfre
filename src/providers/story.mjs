export async function generateStory(input, env = process.env) {
  if ((env.STORY_PROVIDER || 'mock') === 'mock') {
    return { title: input.title || 'Untitled', genre: input.genre || 'mystery', durationSeconds: input.durationSeconds || 45, scenes: input.scenes || [{ id: 's1', duration: 5, location: 'interior', visual: input.visual || 'cinematic scene', dialogue: [] }] };
  }
  const key = env.OPENROUTER_API_KEY;
  if (!key) throw new Error('OPENROUTER_API_KEY is required for real story generation');
  const model = env.STORY_MODEL || 'openai/gpt-4o-mini';
  const prompt = `Create an original ${input.genre || 'mystery'} short film of about ${input.durationSeconds || 45} seconds. Return ONLY JSON with title, genre, durationSeconds and scenes. Each scene must have id, duration, location, visual and dialogue. Each dialogue item must have speaker and text. Use 2-4 recurring characters maximum, strong opening hook and satisfying ending. Avoid copyrighted characters/franchises. Idea: ${input.title || ''}. Visual direction: ${input.visual || ''}`;
  const response = await fetch('https://openrouter.ai/api/v1/chat/completions', { method: 'POST', headers: { Authorization: `Bearer ${key}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ model, temperature: 0.8, response_format: { type: 'json_object' }, messages: [{ role: 'user', content: prompt }] }) });
  if (!response.ok) throw new Error(`Story provider failed: ${response.status} ${await response.text()}`);
  const data = await response.json();
  return JSON.parse(data.choices?.[0]?.message?.content || '{}');
}
