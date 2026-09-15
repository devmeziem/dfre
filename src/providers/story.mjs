function localStorySynthesis(input) {
  const title = input.title || 'The Last Signal';
  const genre = input.genre || 'mystery';
  const durationSeconds = Number(input.durationSeconds || 45);
  const environment = 'A small, cozy old communications room with warm wooden walls, one tall window, a metal desk with an old radio receiver, a desk lamp, shelves of labeled boxes, and a round wall clock. Warm amber practical light comes from the desk lamp while cool blue moonlight enters through the window. Keep this exact architecture, furniture placement, objects, palette and lighting direction throughout the story.';
  const characters = [
    { name: 'Mara', gender: 'female', appearance: 'young adult woman, medium-brown skin, short curly dark hair, round glasses, mustard-yellow jacket over a cream shirt, dark trousers, small silver wristwatch, expressive observant face' },
    { name: 'Eli', gender: 'male', appearance: 'young adult man, deep-brown skin, short neat black hair, teal hoodie under a charcoal utility vest, dark trousers, red canvas sneakers, slim build, calm thoughtful face' }
  ];
  const beats = [
    { visual: 'Mara sits at the metal desk beside Eli, studying the old radio while the room remains quiet and unchanged.', text: `At midnight, ${title} began with a sound nobody had heard in years.` },
    { visual: 'The radio receiver flickers. Mara leans closer while Eli watches the signal meter, with the same desk, shelves, window and clock visible.', text: 'The old radio suddenly crackled, carrying a signal beneath the static.' },
    { visual: 'Mara adjusts the radio dial while Eli checks the wall clock. The warm lamp and cool window light remain consistent.', text: 'Mara turned the dial slowly, and the mysterious signal became clearer.' },
    { visual: 'Eli notices a small envelope beside the radio and shows it to Mara. Both react with surprise in the same room.', text: 'Then Eli found something waiting beside the receiver: an envelope with their names on it.' },
    { visual: 'Mara opens the envelope while Eli stands beside her. The message points toward the old radio, and the environment remains identical.', text: 'Inside was a simple message telling them to listen one more time.' },
    { visual: 'The radio glows softly as Mara and Eli listen together. The room stays visually identical while the clock approaches dawn.', text: 'They listened again, and the final transmission revealed why the signal had returned.' },
    { visual: 'Mara smiles with relief as Eli switches off the radio. Early blue morning light begins to mix with the warm lamp.', text: 'By sunrise, the mystery was solved, and the silence finally felt peaceful.' }
  ];
  const count = Math.max(2, Math.min(beats.length, Math.ceil(durationSeconds / 8)));
  const selected = beats.slice(0, count);
  const perScene = durationSeconds / selected.length;
  return {
    title,
    genre,
    durationSeconds,
    environment,
    characters,
    scenes: selected.map((beat, index) => ({
      id: `s${index + 1}`,
      duration: Number(perScene.toFixed(2)),
      location: 'old communications room',
      visual: beat.visual,
      imagePrompt: `${beat.visual} Stylized 3D animated film frame, non-photorealistic, cinematic vertical composition. Preserve Mara and Eli exactly as established, and preserve the exact communications-room environment bible.`,
      dialogue: [{ speaker: 'Narrator', text: beat.text }]
    }))
  };
}

export async function generateStory(input, env = process.env) {
  if ((env.STORY_PROVIDER || 'cloudflare') === 'mock') return localStorySynthesis(input);

  const account = env.CLOUDFLARE_ACCOUNT_ID;
  const token = env.CLOUDFLARE_API_TOKEN;
  if (!account || !token) return localStorySynthesis(input);

  const model = env.STORY_MODEL || '@cf/meta/llama-3.3-70b-instruct-fp8-fast';
  const prompt = `Create an original ${input.genre || 'mystery'} narrated short film about ${input.durationSeconds || 45} seconds long. Idea: ${input.title || 'The Last Signal'}.
Return ONLY one valid JSON object with this exact top-level structure:
{"title":"...","genre":"...","durationSeconds":45,"environment":"fixed primary setting and visual environment for the whole story","characters":[{"name":"...","gender":"female|male","appearance":"fixed visual description"}],"scenes":[{"id":"s1","duration":5,"location":"...","visual":"...","imagePrompt":"...","dialogue":[{"speaker":"Narrator","text":"..."}]}]}
Rules:
- Create 2-4 recurring original visual characters.
- Each character must have a fixed gender and detailed appearance (age range, skin tone, hair, hairstyle, clothing/colors, and distinctive features).
- Use exactly the same character names throughout the story.
- Never change a character's gender, appearance, clothing identity, or physical traits between scenes.
- Establish ONE primary visual environment/location for the story and treat it as an environment bible: same architecture, room/area layout, walls, windows, doors, furniture, major objects, color palette, time-of-day and lighting direction across scenes.
- Keep scenes in that same primary environment by default. Only change location when the plot absolutely requires it, and if a location change happens, keep that new location consistent for every later scene that uses it.
- Do not randomly replace, redesign, rearrange, or invent the background between scenes. Background continuity is as important as character continuity.
- Every scene imagePrompt must explicitly restate the relevant environment details and the characters present, not merely say "same location".
- THIS V1 USES ONE STORYTELLER VOICE ONLY. Every dialogue entry must use exactly speaker "Narrator". Do not create character dialogue, radio voices, announcers, or other speakers.
- Write natural storytelling narration that describes what happens on screen, with a strong hook, rising tension, and a satisfying ending. Keep narration concise enough to fit the scene duration.
- Give the recurring characters actions, expressions, and interactions in the visuals even though they do not speak.
- Do not use copyrighted characters or franchises.
- Output valid JSON only. No markdown, comments, or extra text.`;

  try {
    const response = await fetch(`https://api.cloudflare.com/client/v4/accounts/${account}/ai/v1/chat/completions`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ model, messages: [{ role: 'user', content: prompt }], response_format: { type: 'json_object' }, temperature: 0.5, max_tokens: 5000 })
    });
    if (!response.ok) throw new Error(`Cloudflare story provider failed: ${response.status} ${await response.text()}`);
    const data = await response.json();
    const content = data.result?.choices?.[0]?.message?.content ?? data.result?.response ?? data.choices?.[0]?.message?.content;
    if (!content) throw new Error('Cloudflare story provider returned no content');
    const text = String(content).trim().replace(/^```(?:json)?\s*/i, '').replace(/\s*```$/i, '').trim();
    const start = text.indexOf('{');
    const end = text.lastIndexOf('}');
    if (start === -1 || end <= start) throw new Error('Cloudflare story provider returned no JSON object');
    const story = JSON.parse(text.slice(start, end + 1));
    if (!story || typeof story !== 'object' || !Array.isArray(story.scenes) || !Array.isArray(story.characters) || story.characters.length < 2) throw new Error('Cloudflare story provider returned an incomplete story');
    return story;
  } catch (error) {
    console.warn(`[STORY] Cloudflare unavailable (${error.message}). Using local synthesis fallback.`);
    return localStorySynthesis(input);
  }
}
