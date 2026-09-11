export async function generateStory(input, env = process.env) {
  if ((env.STORY_PROVIDER || 'cloudflare') === 'mock') {
    return { title: input.title || 'Untitled', genre: input.genre || 'mystery', durationSeconds: input.durationSeconds || 45, scenes: input.scenes || [] };
  }
  const account = env.CLOUDFLARE_ACCOUNT_ID;
  const token = env.CLOUDFLARE_API_TOKEN;
  if (!account || !token) throw new Error('CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN are required');
  const model = env.STORY_MODEL || '@cf/meta/llama-3.3-70b-instruct-fp8-fast';
  const prompt = `Create an original ${input.genre || 'mystery'} short film of about ${input.durationSeconds || 45} seconds. Return ONLY valid JSON with title, genre, durationSeconds and scenes. Each scene needs id, duration, location, visual, imagePrompt and dialogue. Dialogue items need speaker and text. Use 2-4 recurring characters maximum, strong opening hook, clear visual continuity and satisfying ending. Avoid copyrighted characters/franchises. Idea: ${input.title || ''}.`;
  const response = await fetch(`https://api.cloudflare.com/client/v4/accounts/${account}/ai/v1/chat/completions`, {
    method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ model, messages: [{ role: 'user', content: prompt }], temperature: 0.8 })
  });
  if (!response.ok) throw new Error(`Cloudflare story provider failed: ${response.status} ${await response.text()}`);
  const data = await response.json();
  const content = data.result?.choices?.[0]?.message?.content ?? data.result?.response ?? data.choices?.[0]?.message?.content;
  if (!content) throw new Error('Cloudflare story provider returned no content');
  return JSON.parse(content.replace(/^```json\s*|\s*```$/g, ''));
}
