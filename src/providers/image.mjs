import { InferenceClient } from '@huggingface/inference';

export async function generateImage(scene, env = process.env) {
  const provider = env.IMAGE_PROVIDER || 'mock';
  const prompt = `${scene.visual || scene.imagePrompt || ''}. Cinematic vertical composition, consistent character design, detailed lighting, 9:16.`;

  if (provider === 'mock') return { sceneId: scene.id, prompt, path: null };
  if (provider !== 'huggingface') throw new Error(`Unsupported image provider: ${provider}`);

  const token = env.HF_TOKEN;
  if (!token) throw new Error('HF_TOKEN is required for the Hugging Face image provider');

  const model = env.IMAGE_MODEL || 'black-forest-labs/FLUX.1-schnell';
  const hf = new InferenceClient(token);

  try {
    const image = await hf.textToImage({
      provider: env.HF_PROVIDER || 'auto',
      model,
      inputs: prompt,
      parameters: {
        width: 768,
        height: 1344
      }
    });

    const buffer = Buffer.from(await image.arrayBuffer());
    if (!buffer.length) throw new Error('Hugging Face returned an empty image');

    return { sceneId: scene.id, prompt, buffer };
  } catch (error) {
    throw new Error(`Hugging Face image generation failed: ${error.message}`);
  }
}
