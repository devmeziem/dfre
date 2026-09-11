export async function generateImage(scene, env = process.env) {
  const provider = env.IMAGE_PROVIDER || 'mock';
  const prompt = `${scene.visual || scene.imagePrompt || ''}. Cinematic vertical composition, consistent character design, detailed lighting, 9:16.`;
  if (provider === 'mock') return { sceneId: scene.id, prompt, path: null };
  const key = env.HF_TOKEN;
  if (!key) throw new Error('HF_TOKEN is required for the Hugging Face image provider');
  const model = env.IMAGE_MODEL || 'black-forest-labs/FLUX.1-schnell';
  const response = await fetch(`https://api-inference.huggingface.co/models/${model}`, { method: 'POST', headers: { Authorization: `Bearer ${key}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ inputs: prompt }) });
  if (!response.ok) throw new Error(`Image provider failed: ${response.status} ${await response.text()}`);
  const type = response.headers.get('content-type') || '';
  if (!type.includes('image/')) throw new Error(`Image provider returned ${type || 'non-image data'}`);
  const buffer = Buffer.from(await response.arrayBuffer());
  return { sceneId: scene.id, prompt, buffer };
}
