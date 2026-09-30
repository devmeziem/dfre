function localStorySynthesis(input) {
  const title = input.title || 'The Second Lunch';
  const genre = input.genre || 'emotional human story';
  const durationSeconds = Math.max(45, Math.min(120, Number(input.durationSeconds || 90)));
  const environment = 'A bright but natural school cafeteria connected to a quiet school hallway. The cafeteria has long wooden tables, simple chairs, large windows, pale walls, a serving counter and soft midday daylight. The hallway has pale walls, classroom doors, a notice board and a polished floor. Keep each location internally consistent, with the same architecture, furniture placement, major objects, palette and lighting direction whenever it appears.';
  const characters = [
    { name: 'Marcus', gender: 'male', appearance: '14-year-old boy, medium-brown skin, short curly black hair, expressive brown eyes, blue hoodie, dark trousers, black school backpack, slim build' },
    { name: 'Mr. Adeyemi', gender: 'male', appearance: 'older adult school janitor, dark-brown skin, short gray hair, gentle tired face, gray work shirt, dark work trousers, simple black work shoes, sturdy build' }
  ];
  const beats = [
    { visual: 'Busy school cafeteria at lunchtime. Marcus sits alone at the end of a long table, wearing his blue hoodie with his black backpack beside him. He opens the backpack and reveals two identical red lunchboxes; one is on the table and the second remains inside the backpack. Other students are background figures only.', text: 'Every day, Marcus brought two lunches to school. And every day, he made sure nobody saw the second one.' },
    { visual: 'The cafeteria is beginning to empty. Marcus closes the first red lunchbox, places it into his black backpack, waits until the other students leave, then quietly walks toward the cafeteria side door.', text: 'When everyone else left, Marcus stayed behind.' },
    { visual: 'Quiet school hallway connected to the cafeteria. Marcus walks toward Mr. Adeyemi, who is mopping the polished floor. Marcus carries the black backpack and carefully takes the second red lunchbox out. Mr. Adeyemi notices him.', text: 'He was not taking the second lunch home. He was taking it somewhere nobody expected.' },
    { visual: 'In the same hallway, Marcus stands beside Mr. Adeyemi and offers him the second red lunchbox with both hands. Mr. Adeyemi looks surprised, then accepts it with a grateful expression. No one else is nearby.', text: 'Mr. Adeyemi worked at the school every day, but he could not always afford lunch for himself.' },
    { visual: 'The next school day in the same cafeteria. Marcus opens his black backpack and sees two red lunchboxes again. A small handwritten note is attached to one lunchbox. Marcus reads it and looks toward the cafeteria entrance.', text: 'The next day, Marcus found something inside his bag.' },
    { visual: 'Close-up at the same cafeteria table. The handwritten note clearly reads THANK YOU, with a small childlike drawing of two people sitting at a table. In the background, Mr. Adeyemi stands at the cafeteria entrance and gives Marcus a small wave. Marcus smiles and waves back.', text: 'It was only two words. But Marcus kept that note.' },
    { visual: 'One year later in the same cafeteria, Marcus is slightly older but still recognizable, wearing a similar blue hoodie and carrying the same black backpack. He places two red lunchboxes on a table. Four other students sit nearby, and one student quietly slides an extra lunch toward another student who is sitting alone.', text: 'A year later, Marcus still brought two lunches. But he was not the only one anymore.' },
    { visual: 'The same cafeteria is now full of students quietly sharing food. Mr. Adeyemi walks through the room and stops when he sees several students helping others. Marcus looks up at him, and they exchange a warm smile.', text: 'One small act had quietly become a habit, and that habit had become something bigger.' },
    { visual: 'End of school day in the same hallway. Marcus walks past Mr. Adeyemi. They exchange a brief smile. The camera remains behind Marcus as he walks away. Through the open cafeteria doorway, the original red lunchbox remains visible on a table in the warm late-afternoon light.', text: 'You do not always need to change the world. Sometimes, you just need to make sure someone does not feel forgotten.' }
  ];
  const perScene = durationSeconds / beats.length;
  return {
    title,
    genre,
    durationSeconds,
    environment,
    characters,
    scenes: beats.map((beat, index) => ({
      id: `s${index + 1}`,
      duration: Number(perScene.toFixed(2)),
      location: index === 2 || index === 3 || index === 8 ? 'school hallway' : 'school cafeteria',
      visual: beat.visual,
      imagePrompt: `${beat.visual} Stylized cinematic 3D animated film frame, clearly non-photorealistic. Preserve the exact established character designs, props, environment architecture and visual continuity. Vertical 9:16 composition.`,
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
  const prompt = `Create an original standalone animated short film about ${input.durationSeconds || 90} seconds long. Idea: ${input.title || 'The Second Lunch'}. Genre: ${input.genre || 'emotional human story'}.
Return ONLY one valid JSON object with this exact top-level structure:
{"title":"...","genre":"...","durationSeconds":90,"environment":"fixed visual environment bible","characters":[{"name":"...","gender":"male|female","appearance":"fixed visual description"}],"scenes":[{"id":"s1","duration":9,"location":"...","visual":"exactly what is visible and what each character is doing","imagePrompt":"complete image-generation prompt for this scene","dialogue":[{"speaker":"Narrator","text":"..."}]}]}
Rules:
- This is ONE complete standalone story, not an episode and not part of a series.
- Target 45-120 seconds. Prefer 8-10 scenes with enough time for the viewer to understand the story.
- The viewer must understand who the characters are, where they are, what they want, what changes, and why the ending matters without needing another video.
- Build a strong visual hook in the first 3-8 seconds.
- Use a simple cause-and-effect story. Avoid random twists, unexplained supernatural events, dream logic, arbitrary coincidences, or endings that require the viewer to invent missing backstory.
- Give the story a meaningful emotional, practical, human, or thought-provoking payoff. Do not manufacture a twist just for shock.
- Every scene must visually continue from the previous scene. Explicitly describe character position, pose/action, important props, and environment state.
- Use 1-3 recurring original visual characters. Keep exact names and appearances throughout.
- Characters must not speak on screen. They communicate through actions, expressions and body language only.
- Use exactly one storyteller voice: every dialogue entry MUST have speaker exactly "Narrator".
- Establish one or two locations maximum. Keep each location internally consistent. Do not randomly change architecture, furniture, props, time of day or lighting.
- Important props must persist logically. If a character picks up, puts down, opens, closes, gives away or loses an object, the next scene must reflect that change.
- If time passes, explicitly show or narrate the transition so a visual change does not look like a continuity error.
- Every imagePrompt must be self-contained: restate the relevant character appearance, exact environment, important props, action, camera framing, lighting and visual style. Never rely on phrases like "same as previous scene".
- The imagePrompt must describe a stylized cinematic 3D animated film frame, non-photorealistic, vertical 9:16.
- Narration must describe or naturally support what the viewer can actually see. Do not use narration to hide missing visual information.
- The final reveal/payoff must be visible in the final scene, not merely explained.
- No copyrighted characters or franchises.
- Output valid JSON only. No markdown, comments, or extra text.`;

  try {
    const response = await fetch(`https://api.cloudflare.com/client/v4/accounts/${account}/ai/v1/chat/completions`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ model, messages: [{ role: 'user', content: prompt }], response_format: { type: 'json_object' }, temperature: 0.55, max_tokens: 7000 })
    });
    if (!response.ok) throw new Error(`Cloudflare story provider failed: ${response.status} ${await response.text()}`);
    const data = await response.json();
    const content = data.result?.choices?.[0]?.message?.content ?? data.result?.response ?? data.choices?.[0]?.message?.content;
    if (!content) throw new Error('Cloudflare story provider returned no content');
    const text = String(content).trim().replace(/^\`\`\`(?:json)?\s*/i, '').replace(/\s*\`\`\`$/i, '').trim();
    const start = text.indexOf('{');
    const end = text.lastIndexOf('}');
    if (start === -1 || end <= start) throw new Error('Cloudflare story provider returned no JSON object');
    const story = JSON.parse(text.slice(start, end + 1));
    if (!story || typeof story !== 'object' || !Array.isArray(story.scenes) || !Array.isArray(story.characters) || story.characters.length < 1) throw new Error('Cloudflare story provider returned an incomplete story');
    return story;
  } catch (error) {
    console.warn(`[STORY] Cloudflare unavailable (${error.message}). Using local synthesis fallback.`);
    return localStorySynthesis(input);
  }
}
