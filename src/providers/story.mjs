export async function generateStory(input, env = process.env) {
  if ((env.STORY_PROVIDER || 'cloudflare') === 'mock') {
    return {
      title: input.title || 'Untitled',
      genre: input.genre || 'mystery',
      durationSeconds: input.durationSeconds || 45,
      scenes: input.scenes || []
    };
  }

  const account = env.CLOUDFLARE_ACCOUNT_ID;
  const token = env.CLOUDFLARE_API_TOKEN;
  if (!account || !token) throw new Error('CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN are required');

  const model = env.STORY_MODEL || '@cf/meta/llama-3.3-70b-instruct-fp8-fast';
  const prompt = `Create an original ${input.genre || 'mystery'} short film about ${input.durationSeconds || 45} seconds long. Idea: ${input.title || 'The Last Signal'}. Return ONLY a JSON object. It must contain title, genre, durationSeconds, and scenes. scenes must be an array. Each scene must contain id, duration, location, visual, imagePrompt, and dialogue. dialogue must be an array of objects containing speaker and text. Use 2-4 recurring original characters, a strong opening hook, visual continuity, and a satisfying ending. Keep dialogue concise. Do not use copyrighted characters or franchises.`;

  const response = await fetch(`https://api.cloudflare.com/client/v4/accounts/${account}/ai/v1/chat/completions`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      model,
      messages: [{ role: 'user', content: prompt }],
      response_format: { type: 'json_object' },
      temperature: 0.7,
      max_tokens: 4000
    })
  });

  if (!response.ok) throw new Error(`Cloudflare story provider failed: ${response.status} ${await response.text()}`);
  const data = await response.json();
  const content = data.result?.choices?.[0]?.message?.content ?? data.result?.response ?? data.choices?.[0]?.message?.content;
  if (!content) throw new Error('Cloudflare story provider returned no content');

  const text = String(content).trim().replace(/^```(?:json)?\s*/i, '').replace(/\s*```$/i, '').trim();
  const start = text.indexOf('{');
  const end = text.lastIndexOf('}');
  if (start === -1 || end <= start) throw new Error(`Cloudflare story provider returned no JSON object: ${text.slice(0, 500)}`);

  const jsonText = text.slice(start, end + 1);
  let story;
  try {
    story = JSON.parse(jsonText);
  } catch (error) {
    throw new Error(`Cloudflare story provider returned invalid JSON: ${error.message}. Response: ${jsonText.slice(0, 1000)}`);
  }

  if (!story || typeof story !== 'object' || !Array.isArray(story.scenes)) {
    throw new Error('Cloudflare story provider returned JSON without a scenes array');
  }

  return story;
}
