import { EdgeTTS } from 'node-edge-tts';

const DEFAULT_VOICES = {
  narrator: 'en-US-EmmaMultilingualNeural',
  mira: 'en-US-AndrewMultilingualNeural'
};

export async function generateVoice(line, voice, env = process.env) {
  if ((env.VOICE_PROVIDER || 'edge') === 'mock') {
    return { speaker: line.speaker, voice, text: line.text, audio: null };
  }

  if ((env.VOICE_PROVIDER || 'edge') !== 'edge') {
    throw new Error(`Unsupported voice provider: ${env.VOICE_PROVIDER}`);
  }

  const speakerKey = String(line.speaker || voice || 'narrator').toLowerCase().replace(/[^a-z0-9]/g, '_');
  const voiceId = env[`EDGE_VOICE_${speakerKey.toUpperCase()}`] || DEFAULT_VOICES[speakerKey] || env.EDGE_VOICE_NARRATOR || DEFAULT_VOICES.narrator;
  const tts = new EdgeTTS(String(line.text || ''), voiceId, {
    rate: env.EDGE_TTS_RATE || '+0%',
    volume: env.EDGE_TTS_VOLUME || '+0%'
  });
  const result = await tts.synthesize();
  if (!result?.audio) throw new Error(`Edge TTS returned no audio for ${speakerKey}`);

  return {
    speaker: line.speaker,
    voice: voiceId,
    text: line.text,
    audioBuffer: Buffer.from(await result.audio.arrayBuffer()),
    subtitles: result.subtitle || []
  };
}
