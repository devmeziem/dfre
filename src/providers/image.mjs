export async function generateImage(scene, env = process.env) {
  const provider = env.IMAGE_PROVIDER || "mock";
  if (provider !== "mock") throw new Error(`Unsupported IMAGE_PROVIDER: ${provider}`);
  return { sceneId: scene.id, prompt: `${scene.visual}. Cinematic vertical composition, consistent character design, detailed lighting, 9:16.` };
}
