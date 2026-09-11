export async function generateVoice(line, voice, env = process.env) {
  const provider = env.VOICE_PROVIDER || 'mock';
  if (provider === 'mock') return { speaker: line.speaker, voice, text: line.text, audio: null };
  const key = env.ELEVENLABS_API_KEY;
  if (!key) throw new Error('ELEVENLABS_API_KEY is required for the voice provider');
  const speakerKey = String(line.speaker || voice || 'narrator').toUpperCase().replace(/[^A-Z0-9]/g, '_');
  const voiceId = env[`VOICE_${speakerKey}`] || (voice && voice !== 'default' ? voice : env.ELEVENLABS_VOICE_ID);
  if (!voiceId) throw new Error(`No ElevenLabs voice ID configured for ${speakerKey}`);
  const response = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${voiceId}`, { method: 'POST', headers: { 'xi-api-key': key, 'Content-Type': 'application/json', Accept: 'audio/mpeg' }, body: JSON.stringify({ text: line.text, model_id: env.ELEVENLABS_MODEL || 'eleven_multilingual_v2' }) });
  if (!response.ok) throw new Error(`Voice provider failed: ${response.status} ${await response.text()}`);
  return { speaker: line.speaker, voice: voiceId, text: line.text, audioBuffer: Buffer.from(await response.arrayBuffer()) };
}
