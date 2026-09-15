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

async function pollinationsImage(prompt, env) {
  const width = Number(env.IMAGE_WIDTH || 512);
  const height = Number(env.IMAGE_HEIGHT || 896);
  const model = env.POLLINATIONS_IMAGE_MODEL || 'flux';
  const url = new URL(`https://image.pollinations.ai/prompt/${encodeURIComponent(prompt)}`);
  url.searchParams.set('model', model);
  url.searchParams.set('width', String(width));
  url.searchParams.set('height', String(height));
  url.searchParams.set('nologo', 'true');
  url.searchParams.set('safe', 'true');
  const response = await fetch(url, { signal: AbortSignal.timeout(Math.max(30, Number(env.POLLINATIONS_TIMEOUT_SECONDS || 180)) * 1000 });
  if (!response.ok) throw new Error(`Pollinations image fallback failed: HTTP ${response.status}`);
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.startsWith('image/')) throw new Error(`Pollinations returned non-image content (${contentType || 'unknown'})`);
  return Buffer.from(await response.arrayBuffer());
}

function continuitySynthesisPrompt(scene) {
  const environment = scene.environment || scene.environmentBible || 'the established primary story environment';
  const characters = Array.isArray(scene.characters)
    ? scene.characters.map((c) => `${c.name}: ${c.gender}; ${c.appearance}`).join(' | ')
    : 'Preserve all established recurring characters exactly as described in the story.';
  const base = scene.visual || scene.imagePrompt || '';
  return `${base}. SYNTHESIS FALLBACK: create an original, non-photorealistic stylized 3D animated-film frame. Preserve visual continuity exactly across the series. ENVIRONMENT BIBLE: ${environment}. CHARACTERS: ${characters}. Keep the same faces, hair, skin tones, ages, body proportions, clothing identities and distinctive features. Keep the same architecture, room layout, walls, windows, doors, furniture, major objects, palette, time of day and lighting direction. Change only the pose, expression, camera framing and ordinary story action required for this scene. Do not redesign characters, replace people, move furniture, invent a new location, or drift to a different visual universe. Clean shapes, expressive animation, polished cinematic lighting, vertical 9:16.`;
}

function safePrompt(scene) {
  const base = scene.visual || scene.imagePrompt || '';
  return `${base}. ORIGINAL FAMILY-FRIENDLY STYLIZED 3D ANIMATION. Non-photorealistic animated film frame, clean shapes, expressive friendly characters, cinematic lighting. Use image 0 as the visual identity and environment reference. Preserve the established character designs exactly: same face, hair, skin tone, age, body proportions, clothing identity and distinctive features. Preserve the established environment architecture, layout, furniture, major objects, palette, time of day and lighting direction. Change only pose, expression, camera framing and ordinary story action. Do not redesign or replace the background or characters. Show only the ordinary story action needed for this scene. No violence, injury, weapons, blood, gore, frightening imagery, sexual content, or dangerous activity. Vertical 9:16.`;
}

export async function generateCharacterReference(characters, environment = '', env = process.env) {
  const provider = env.IMAGE_PROVIDER || 'mock';
  const description = characters.map((c) => `${c.name}: ${c.gender}; ${c.appearance}`).join('\n');
  const environmentText = String(environment || '').trim() || 'a consistent primary story environment';
  const prompt = `Create an ORIGINAL stylized 3D animated visual bible reference sheet for a cinematic short film. Non-photorealistic animation only: appealing designed characters, slightly rounded forms, expressive faces, clean shapes, polished animated-film lighting, not live action, not a photograph. Show every named character clearly and separately in the SAME PRIMARY ENVIRONMENT described below, so later scenes can preserve both character identity and background continuity. Include recognizable fixed architecture, room/area layout, walls, windows, doors, furniture, major objects, color palette, time-of-day and lighting direction. Do not add extra people. Preserve the exact character appearances described below.\n\nPRIMARY ENVIRONMENT:\n${environmentText}\n\nCHARACTERS:\n${description}`;
  if (provider === 'mock') return { prompt, buffer: null };
  if (provider !== 'cloudflare') throw new Error(`Unsupported image provider: ${provider}`);

  try {
    console.log(`[CF] Generating stylized character/environment reference with ${modelFor(env)}`);
    const buffer = await cloudflareImage({ prompt, width: 448, height: 448 }, env);
    console.log('[CF] Character/environment reference generated');
    return { prompt, buffer };
  } catch (error) {
    console.warn(`[CF] Character/environment reference unavailable (${error.message}). Trying synthesis fallback.`);
    try {
      const buffer = await pollinationsImage(prompt, { ...env, IMAGE_WIDTH: 448, IMAGE_HEIGHT: 448 });
      console.log('[SYNTH] Character/environment reference generated with Pollinations fallback');
      return { prompt, buffer };
    } catch (fallbackError) {
      console.warn(`[SYNTH] Reference fallback unavailable (${fallbackError.message}). Continuing without a reference image.`);
      return { prompt, buffer: null };
    }
  }
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
    if (error.cloudflareFlagged) {
      console.warn(`[CF] ${scene.id} was flagged. Retrying once with the same visual reference.`);
      try {
        const fallbackPrompt = safePrompt(scene);
        const fallbackFields = {
          prompt: fallbackPrompt,
          width: Number(env.IMAGE_WIDTH || 512),
          height: Number(env.IMAGE_HEIGHT || 896),
          ...(scene.referenceBuffer ? { input_image_0: scene.referenceBuffer } : {})
        };
        const buffer = await cloudflareImage(fallbackFields, env);
        console.log(`[CF] Safe fallback image generated for ${scene.id} with visual reference preserved`);
        return { sceneId: scene.id, prompt: fallbackPrompt, buffer };
      } catch (safeError) {
        console.warn(`[CF] Safe retry for ${scene.id} failed: ${safeError.message}`);
      }
    } else {
      console.warn(`[CF] ${scene.id} failed: ${error.message}`);
    }

    const synthesisPrompt = continuitySynthesisPrompt(scene);
    console.warn(`[SYNTH] Trying Pollinations fallback for ${scene.id} with continuity synthesis prompt.`);
    try {
      const buffer = await pollinationsImage(synthesisPrompt, env);
      console.log(`[SYNTH] Image generated for ${scene.id} with Pollinations fallback`);
      return { sceneId: scene.id, prompt: synthesisPrompt, buffer };
    } catch (fallbackError) {
      throw new Error(`Image generation failed for ${scene.id}. Cloudflare: ${error.message}. Pollinations fallback: ${fallbackError.message}`);
    }
  }
}
