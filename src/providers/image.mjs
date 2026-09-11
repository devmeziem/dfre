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
    if (Buffer.isBuffer(value)) {
      form.append(key, new Blob([value], { type: 'image/png' }), `${key}.png`);
    } else {
      form.append(key, String(value));
    }
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), Math.max(30, Number(env.CLOUDFLARE_IMAGE_TIMEOUT_SECONDS || 180)) * 1000);
  try {
    const response = await fetch(`https://api.cloudflare.com/client/v4/accounts/${account}/ai/run/${model}`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: form,
      signal: controller.signal
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok || !data.success) {
      const detail = data.errors?.map((e) => e.message).join('; ') || `HTTP ${response.status}`;
      throw new Error(detail);
    }
    const encoded = typeof data.result === 'string' ? data.result : data.result?.image;
    if (!encoded) throw new Error('Cloudflare returned no image data');
    return Buffer.from(String(encoded).replace(/^data:image\/[^;]+;base64,/, ''), 'base64');
  } finally {
    clearTimeout(timeout);
  }
}

export async function generateCharacterReference(characters, env = process.env) {
  const provider = env.IMAGE_PROVIDER || 'mock';
  const description = characters.map((c) => `${c.name}: ${c.gender}; ${c.appearance}`).join('\n');
  const prompt = `Create a clean cinematic character reference sheet for an original short film. Show every named character clearly and separately, waist-up or full-body, front-facing, neutral pose, simple neutral background. Preserve the exact appearance described below. Do not add extra people. This image is a visual identity reference for later scenes.\n\n${description}`;

  if (provider === 'mock') return { prompt, buffer: null };
  if (provider === 'cloudflare') {
    console.log(`[CF] Generating character reference with ${modelFor(env)}`);
    const buffer = await cloudflareImage({ prompt, width: 448, height: 448 }, env);
    console.log('[CF] Character reference generated');
    return { prompt, buffer };
  }
  if (provider === 'huggingface') {
    throw new Error('Hugging Face image generation is disabled for this build; use IMAGE_PROVIDER=cloudflare');
  }
  throw new Error(`Unsupported image provider: ${provider}`);
}

export async function generateImage(scene, env = process.env) {
  const provider = env.IMAGE_PROVIDER || 'mock';
  const prompt = `${scene.visual || scene.imagePrompt || ''}. Use image 0 as the character identity reference. Keep every referenced character the exact same person: same face, hair, skin tone, age, body proportions, clothing identity and distinctive features. Change only pose, expression, camera framing, location and action required by this scene. Do not introduce replacement people. Cinematic vertical composition, detailed lighting, natural anatomy, 9:16.`;

  if (provider === 'mock') return { sceneId: scene.id, prompt, path: null };
  if (provider !== 'cloudflare') throw new Error(`Unsupported image provider: ${provider}`);

  console.log(`[CF] Generating ${scene.id} with ${modelFor(env)}${scene.referenceBuffer ? ' + character reference' : ''}`);
  const fields = {
    prompt,
    width: Number(env.IMAGE_WIDTH || 768),
    height: Number(env.IMAGE_HEIGHT || 1344)
  };
  if (scene.referenceBuffer) fields.input_image_0 = scene.referenceBuffer;
  const buffer = await cloudflareImage(fields, env);
  console.log(`[CF] Image generated for ${scene.id}`);
  return { sceneId: scene.id, prompt, buffer };
}
