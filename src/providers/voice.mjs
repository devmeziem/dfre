import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { randomUUID } from 'node:crypto';
import { EdgeTTS } from 'node-edge-tts';

const DEFAULT_VOICES = {
  narrator: 'en-US-AriaNeural',
  mira: 'en-US-GuyNeural'
};

export async function generateVoice(line, voice, env = process.env) {
  const provider = env.VOICE_PROVIDER || 'edge';
  if (provider === 'mock') {
    return { speaker: line.speaker, voice, text: line.text, audio: null };
  }
  if (provider !== 'edge') {
    throw new Error(`Unsupported voice provider: ${provider}`);
  }

  const speakerKey = String(line.speaker || voice || 'narrator')
    .toLowerCase()
    .replace(/[^a-z0-9]/g, '_');
  const voiceId = env[`EDGE_VOICE_${speakerKey.toUpperCase()}`]
    || DEFAULT_VOICES[speakerKey]
    || env.EDGE_VOICE_NARRATOR
    || DEFAULT_VOICES.narrator;

  const output = path.join(os.tmpdir(), `dfre-${randomUUID()}.mp3`);
  try {
    const tts = new EdgeTTS({
      voice: voiceId,
      lang: env.EDGE_TTS_LANG || 'en-US',
      outputFormat: 'audio-24khz-48kbitrate-mono-mp3',
      rate: env.EDGE_TTS_RATE || 'default',
      volume: env.EDGE_TTS_VOLUME || 'default',
      pitch: env.EDGE_TTS_PITCH || 'default',
      timeout: 30000
    });
    await tts.ttsPromise(String(line.text || ''), output);
    const audioBuffer = await fs.readFile(output);
    if (!audioBuffer.length) throw new Error('Edge TTS returned an empty audio file');
    return { speaker: line.speaker, voice: voiceId, text: line.text, audioBuffer };
  } finally {
    await fs.rm(output, { force: true }).catch(() => {});
  }
}
