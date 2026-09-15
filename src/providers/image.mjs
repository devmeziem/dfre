function requireCloudflare(env) {
  const account = env.CLOUDFLARE_ACCOUNT_ID;
  const token = env.CLOUDFLARE_API_TOKEN;
  if (!account || !token) throw new Error('CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN are required for the Cloudflare image provider');
  return { account, token };
}

function modelFor(env) {
  return env.CLOUDFLARE_IMAGE_MODEL || '@cf/black-forest-labs/flux-2-klein-4b';
}

async function cloudflareImage(fields, env) {
  const { account, token } = requireCloudflare(env);
  const model = modelFor(env);
  const form = new FormData();
  for (const [key, value] of Object.entries(fields)) {
    if (value == null) continue;
    if (Buffer.isBuffer(value)) form.append(key, new Blob([value], { type: 'image/png' }), `${key}.png`);
    else form.append(key, String(value));
  }
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), Math.max(30, Number(env.CLOUDFLARE_IMAGE_TIMEOUT_SECONDS || 180)) * 1000);
  try {
    const response = await fetch(`https://api.cloudflare.com/client/v4/accounts/${account}/ai/run/${model}`, { method: 'POST', headers: { Authorization: `Bearer ${token}` }, body: form, signal: controller.signal });
    const data = await response.json().catch(() => ({}));
    if (!response.ok || !data.success) {
      const detail = data.errors?.map((e) => e.message).join('; ') || `HTTP ${response.status}`;
      const error = new Error(detail);
      error.cloudflareFlagged = /flagged|safety|content/i.test(detail);
      throw error;
    }
    const encoded = typeof data.result === 'string' ? data.result : data.result?.image;
    if (!encoded) throw new Error('Cloudflare returned no image data');
    return Buffer.from(String(encoded).replace(/^data:image\/[^;]+;base64,/, ''), 'base64');
  } finally { clearTimeout(timeout); }
}

function safePrompt(scene) {
  const base = scene.visual || scene.imagePrompt || '';
  return `${base}. ORIGINAL FAMILY-FRIENDLY STYLIZED 3D ANIMATION. Non-photorealistic animated film frame, clean shapes, expressive friendly characters, cinematic lighting. Show only the ordinary story action needed for this scene. No violence, injury, weapons, blood, gore, frightening imagery, sexual content, or dangerous activity. Preserve the established character designs and environment continuity. Vertical 9:16.`;
}

export async function generateCharacterReference(characters, environment = '', env = process.env) {
  const provider = env.IMAGE_PROVIDER || 'mock';
  const description = characters.map((c) => `${c.name}: ${c.gender}; ${c.appearance}`).join('\n');
  const environmentText = String(environment || '').trim() || 'a consistent primary story environment';
  const prompt = `Create an ORIGINAL stylized 3D animated visual bible reference sheet for a cinematic short film. Non-photorealistic animation only: appealing designed characters, slightly rounded forms, expressive faces, clean shapes, polished animated-film lighting, not live action, not a photograph. Show every named character clearly and separately in the SAME PRIMARY ENVIRONMENT described below, so later scenes can preserve both character identity and background continuity. Include recognizable fixed architecture, room/area layout, walls, windows, doors, furniture, major objects, color palette, time-of-day and lighting direction. Do not add extra people. Preserve the exact character appearances described below.\n\nPRIMARY ENVIRONMENT:\n${environmentText}\n\nCHARACTERS:\n${description}`;
  if (provider === 'mock') return { prompt, buffer: null };
  if (provider === 'cloudflare') {
    console.log(`[CF] Generating stylized character/environment reference with ${modelFor(env)}`);
    const buffer = await cloudflareImage({ prompt, width: 448, height: 448 }, env);
    console.log('[CF] Character/environment reference generated');
    return { prompt, buffer };
  }
  if (provider === 'huggingface') throw new Error('Hugging Face image generation is disabled for this build; use IMAGE_PROVIDER=cloudflare');
  throw new Error(`Unsupported image provider: ${provider}`);
}

export async function generateImage(scene, env = process.env) {
  const provider = env.IMAGE_PROVIDER || 'mock';
  if (provider === 'mock') return { sceneId: scene.id, prompt: scene.imagePrompt || scene.visual || '', path: null };
  if (provider !== 'cloudflare') throw new Error(`Unsupported image provider: ${provider}`);

  const normalPrompt = `${scene.visual || scene.imagePrompt || ''}. ORIGINAL STYLIZED 3D ANIMATED FILM LOOK, clearly non-photorealistic and not live action. Use image 0 as the visual identity and environment reference. Keep every referenced character the exact same designed person: same face, hair, skin tone, age, body proportions, clothing identity and distinctive features. Keep the established environment architecture, layout, furniture, major objects, palette, time of day and lighting direction consistent with the reference. Change only pose, expression, camera framing and story action required by this scene. Do not redesign or replace the background. Do not introduce replacement people. Expressive animation, polished cinematic lighting, clean shapes, natural readable anatomy, cinematic vertical composition, 9:16.`;
  const fields = { prompt: normalPrompt, width: Number(env.IMAGE_WIDTH || 512), height: Number(env.IMAGE_HEIGHT || 896) };
  if (scene.referenceBuffer) fields.input_image_0 = scene.referenceBuffer;

  console.log(`[CF] Generating ${scene.id} with ${modelFor(env)}${scene.referenceBuffer ? ' + visual reference' : ''}`);
  try {
    const buffer = await cloudflareImage(fields, env);
    console.log(`[CF] Image generated for ${scene.id}`);
    return { sceneId: scene.id, prompt: normalPrompt, buffer };
  } catch (error) {
    if (!error.cloudflareFlagged) throw error;
    console.warn(`[CF] ${scene.id} was flagged. Retrying once with a neutral prompt and no reference image.`);
    const fallbackPrompt = safePrompt(scene);
    const fallbackFields = { prompt: fallbackPrompt, width: Number(env.IMAGE_WIDTH || 512), height: Number(env.IMAGE_HEIGHT || 896) };
    const buffer = await cloudflareImage(fallbackFields, env);
    console.log(`[CF] Safe fallback image generated for ${scene.id}`);
    return { sceneId: scene.id, prompt: fallbackPrompt, buffer };
  }
}
