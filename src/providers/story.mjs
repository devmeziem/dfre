export async function generateStory(input, env = process.env) {
  if ((env.STORY_PROVIDER || 'cloudflare') === 'mock') {
    return {
      title: input.title || 'Untitled',
      genre: input.genre || 'mystery',
      durationSeconds: input.durationSeconds || 45,
      characters: input.characters || [],
      scenes: input.scenes || []
    };
  }

  const account = env.CLOUDFLARE_ACCOUNT_ID;
  const token = env.CLOUDFLARE_API_TOKEN;
  if (!account || !token) throw new Error('CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN are required');

  const model = env.STORY_MODEL || '@cf/meta/llama-3.3-70b-instruct-fp8-fast';
  const prompt = `Create an original ${input.genre || 'mystery'} narrated short film about ${input.durationSeconds || 45} seconds long. Idea: ${input.title || 'The Last Signal'}.
Return ONLY one valid JSON object with this exact top-level structure:
{"title":"...","genre":"...","durationSeconds":45,"characters":[{"name":"...","gender":"female|male","appearance":"fixed visual description"}],"scenes":[{"id":"s1","duration":5,"location":"...","visual":"...","imagePrompt":"...","dialogue":[{"speaker":"Narrator","text":"..."}]}]}
Rules:
- Create 2-4 recurring original visual characters.
- Each character must have a fixed gender and detailed appearance (age range, skin tone, hair, hairstyle, clothing/colors, and distinctive features).
- Use exactly the same character names throughout the story.
- Never change a character's gender, appearance, clothing identity, or physical traits between scenes.
- Every scene imagePrompt must describe the correct recurring characters and preserve their fixed appearance.
- THIS V1 USES ONE STORYTELLER VOICE ONLY. Every dialogue entry must use exactly speaker "Narrator". Do not create character dialogue, radio voices, announcers, or other speakers.
- Write natural storytelling narration that describes what happens on screen, with a strong hook, rising tension, and a satisfying ending. Keep narration concise enough to fit the scene duration.
- Give the recurring characters actions, expressions, and interactions in the visuals even though they do not speak.
- Do not use copyrighted characters or franchises.
- Output valid JSON only. No markdown, comments, or extra text.`;

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
      temperature: 0.5,
      max_tokens: 5000
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
  if (!Array.isArray(story.characters) || story.characters.length < 2) {
    throw new Error('Cloudflare story provider returned fewer than 2 characters');
  }

  return story;
}
