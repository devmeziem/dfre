import { InferenceClient } from '@huggingface/inference';

function makeClient(env) {
  const token = env.HF_TOKEN;
  if (!token) throw new Error('HF_TOKEN is required for the Hugging Face image provider');
  const timeout = Number(env.HF_TIMEOUT_SECONDS || 180);
  return new InferenceClient(token, { timeout });
}

async function toBuffer(blob) {
  const buffer = Buffer.from(await blob.arrayBuffer());
  if (!buffer.length) throw new Error('Hugging Face returned an empty image');
  return buffer;
}

export async function generateCharacterReference(characters, env = process.env) {
  const provider = env.IMAGE_PROVIDER || 'mock';
  const description = characters.map((c) => `${c.name}: ${c.gender}; ${c.appearance}`).join('\n');
  const prompt = `Create a clean cinematic character reference sheet for an original short film. Show every named character as a clearly separated full-body portrait, mostly facing forward, with neutral expression and simple neutral background. Preserve the exact appearance described below. Do not add extra people. This reference will be used to keep character identity consistent across later scenes.\n\n${description}`;

  if (provider === 'mock') return { prompt, buffer: null };
  if (provider !== 'huggingface') throw new Error(`Unsupported image provider: ${provider}`);

  const hf = makeClient(env);
  const model = env.IMAGE_REFERENCE_MODEL || 'black-forest-labs/FLUX.1-schnell';
  const providerName = env.HF_REFERENCE_PROVIDER || 'nscale';
  try {
    const image = await hf.textToImage({
      provider: providerName,
      model,
      inputs: prompt,
      parameters: { width: 768, height: 1344 }
    });
    return { prompt, buffer: await toBuffer(image) };
  } catch (error) {
    throw new Error(`Hugging Face character reference generation failed (${providerName}/${model}): ${error.message}`);
  }
}

export async function generateImage(scene, env = process.env) {
  const provider = env.IMAGE_PROVIDER || 'mock';
  const prompt = `${scene.visual || scene.imagePrompt || ''}. Cinematic vertical composition, consistent character design, detailed lighting, 9:16.`;

  if (provider === 'mock') return { sceneId: scene.id, prompt, path: null };
  if (provider !== 'huggingface') throw new Error(`Unsupported image provider: ${provider}`);

  const hf = makeClient(env);
  const model = env.IMAGE_MODEL || 'black-forest-labs/FLUX.1-Kontext-dev';
  const providerName = env.HF_IMAGE_PROVIDER || 'fal-ai';
  try {
    let image;
    if (scene.referenceBuffer) {
      image = await hf.imageToImage({
        provider: providerName,
        model,
        inputs: new Blob([scene.referenceBuffer], { type: 'image/png' }),
        parameters: {
          prompt,
          target_size: { width: 768, height: 1344 }
        }
      });
    } else {
      image = await hf.textToImage({
        provider: providerName,
        model: env.IMAGE_TEXT_MODEL || 'black-forest-labs/FLUX.1-schnell',
        inputs: prompt,
        parameters: { width: 768, height: 1344 }
      });
    }
    return { sceneId: scene.id, prompt, buffer: await toBuffer(image) };
  } catch (error) {
    throw new Error(`Hugging Face image generation failed (${providerName}/${model}): ${error.message}`);
  }
}
