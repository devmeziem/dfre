import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { randomUUID } from 'node:crypto';
import { EdgeTTS } from 'node-edge-tts';

const DEFAULT_VOICES = {
  narrator: 'en-US-AriaNeural',
  female1: 'en-US-AriaNeural',
  male1: 'en-US-GuyNeural',
  female2: 'en-US-JennyNeural',
  male2: 'en-US-DavisNeural',
  female3: 'en-US-SaraNeural',
  male3: 'en-US-JasonNeural',
  female4: 'en-US-MichelleNeural',
  male4: 'en-US-TonyNeural'
};

const VOICE_PROFILES = {
  'en-US-AriaNeural': { rate: '-4%', pitch: '-2Hz' },
  'en-US-GuyNeural': { rate: '-8%', pitch: '-18Hz' },
  'en-US-JennyNeural': { rate: '+7%', pitch: '+12Hz' },
  'en-US-DavisNeural': { rate: '-3%', pitch: '-10Hz' },
  'en-US-SaraNeural': { rate: '+3%', pitch: '+8Hz' },
  'en-US-JasonNeural': { rate: '-6%', pitch: '-6Hz' },
  'en-US-MichelleNeural': { rate: '+5%', pitch: '+15Hz' },
  'en-US-TonyNeural': { rate: '+2%', pitch: '-14Hz' }
};

function resolveVoice(line, voice, env) {
  const requested = String(voice || '').trim();
  const speakerKey = String(line.speaker || 'narrator').toLowerCase().replace(/[^a-z0-9]/g, '_');
  return requested.includes('-') && requested.endsWith('Neural')
    ? requested
    : env[`EDGE_VOICE_${speakerKey.toUpperCase()}`] || DEFAULT_VOICES[requested.toLowerCase()] || DEFAULT_VOICES[speakerKey] || env.EDGE_VOICE_NARRATOR || DEFAULT_VOICES.narrator;
}

export async function generateVoice(line, voice, env = process.env) {
  const provider = env.VOICE_PROVIDER || 'edge';
  if (provider === 'mock') return { speaker: line.speaker, voice, text: line.text, audio: null };
  if (provider !== 'edge') throw new Error(`Unsupported voice provider: ${provider}`);

  const voiceId = resolveVoice(line, voice, env);
  const profile = VOICE_PROFILES[voiceId] || { rate: env.EDGE_TTS_RATE || 'default', pitch: env.EDGE_TTS_PITCH || 'default' };
  const output = path.join(os.tmpdir(), `dfre-${randomUUID()}.mp3`);
  const timeout = Number(env.EDGE_TTS_TIMEOUT_MS || 60000);

  try {
    console.log(`[TTS] Generating ${line.speaker} with ${voiceId} (${profile.rate}, ${profile.pitch})`);
    const tts = new EdgeTTS({
      voice: voiceId,
      lang: env.EDGE_TTS_LANG || 'en-US',
      outputFormat: 'audio-24khz-48kbitrate-mono-mp3',
      rate: profile.rate,
      volume: env.EDGE_TTS_VOLUME || 'default',
      pitch: profile.pitch,
      timeout
    });
    await tts.ttsPromise(String(line.text || ''), output);
    const audioBuffer = await fs.readFile(output);
    if (!audioBuffer.length) throw new Error('Edge TTS returned an empty audio file');
    console.log(`[TTS] Completed ${line.speaker}`);
    return { speaker: line.speaker, voice: voiceId, text: line.text, audioBuffer };
  } finally {
    await fs.rm(output, { force: true }).catch(() => {});
  }
}
