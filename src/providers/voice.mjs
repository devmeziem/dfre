export async function generateVoice(line, voice, env = process.env) {
  const provider = env.VOICE_PROVIDER || "mock";
  if (provider !== "mock") throw new Error(`Unsupported VOICE_PROVIDER: ${provider}`);
  return { speaker: line.speaker, voice, text: line.text, audio: null };
}
