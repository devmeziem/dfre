import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { randomUUID } from 'node:crypto';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { EdgeTTS } from 'node-edge-tts';

const execFileAsync = promisify(execFile);

const DEFAULT_VOICES = {
  narrator: 'en-US-AriaNeural',
  female1: 'en-US-AriaNeural', male1: 'en-US-GuyNeural',
  female2: 'en-US-JennyNeural', male2: 'en-US-DavisNeural',
  female3: 'en-US-SaraNeural', male3: 'en-US-JasonNeural',
  female4: 'en-US-MichelleNeural', male4: 'en-US-TonyNeural'
};

const EDGE_PROFILES = {
  'en-US-AriaNeural': { rate: '-4%', pitch: '-2Hz' },
  'en-US-GuyNeural': { rate: '-8%', pitch: '-18Hz' },
  'en-US-JennyNeural': { rate: '+7%', pitch: '+12Hz' },
  'en-US-DavisNeural': { rate: '-3%', pitch: '-10Hz' },
  'en-US-SaraNeural': { rate: '+3%', pitch: '+8Hz' },
  'en-US-JasonNeural': { rate: '-6%', pitch: '-6Hz' },
  'en-US-MichelleNeural': { rate: '+5%', pitch: '+15Hz' },
  'en-US-TonyNeural': { rate: '+2%', pitch: '-14Hz' }
};

const LOCAL_PROFILES = {
  'en-US-AriaNeural': { voice: 'en-us', rate: 155, pitch: 48 },
  'en-US-GuyNeural': { voice: 'en-gb', rate: 135, pitch: 38 },
  'en-US-JennyNeural': { voice: 'en-us', rate: 175, pitch: 62 },
  'en-US-DavisNeural': { voice: 'en-gb', rate: 145, pitch: 35 },
  'en-US-SaraNeural': { voice: 'en-us', rate: 165, pitch: 58 },
  'en-US-JasonNeural': { voice: 'en-sc', rate: 130, pitch: 30 },
  'en-US-MichelleNeural': { voice: 'en-au', rate: 150, pitch: 65 },
  'en-US-TonyNeural': { voice: 'en-gb', rate: 180, pitch: 42 }
};

function resolveVoice(line, voice, env) {
  const requested = String(voice || '').trim();
  const speakerKey = String(line.speaker || 'narrator').toLowerCase().replace(/[^a-z0-9]/g, '_');
  return requested.includes('-') && requested.endsWith('Neural')
    ? requested
    : env[`EDGE_VOICE_${speakerKey.toUpperCase()}`] || DEFAULT_VOICES[requested.toLowerCase()] || DEFAULT_VOICES[speakerKey] || env.EDGE_VOICE_NARRATOR || DEFAULT_VOICES.narrator;
}

async function generateLocal(line, voiceId, outputBase) {
  const profile = LOCAL_PROFILES[voiceId] || { voice: 'en-us', rate: 160, pitch: 50 };
  const wav = `${outputBase}.wav`;
  const mp3 = `${outputBase}.mp3`;
  console.log(`[TTS] Local voice ${voiceId} for ${line.speaker} (${profile.voice}, ${profile.rate}wpm, pitch ${profile.pitch})`);
  try {
    await execFileAsync('espeak-ng', ['-v', profile.voice, '-s', String(profile.rate), '-p', String(profile.pitch), '-a', '150', '-w', wav, String(line.text || '')], { timeout: 15000 });
    await execFileAsync('ffmpeg', ['-y', '-hide_banner', '-loglevel', 'error', '-i', wav, '-codec:a', 'libmp3lame', '-b:a', '64k', mp3], { timeout: 15000 });
    const audioBuffer = await fs.readFile(mp3);
    if (!audioBuffer.length) throw new Error('Local TTS returned an empty audio file');
    console.log(`[TTS] Completed ${line.speaker}`);
    return { speaker: line.speaker, voice: voiceId, text: line.text, audioBuffer };
  } finally {
    await fs.rm(wav, { force: true }).catch(() => {});
    await fs.rm(mp3, { force: true }).catch(() => {});
  }
}

async function generateEdge(line, voiceId, profile, env, output) {
  const tts = new EdgeTTS({
    voice: voiceId,
    lang: env.EDGE_TTS_LANG || 'en-US',
    outputFormat: 'audio-24khz-48kbitrate-mono-mp3',
    rate: profile.rate,
    volume: env.EDGE_TTS_VOLUME || 'default',
    pitch: profile.pitch,
    timeout: Number(env.EDGE_TTS_TIMEOUT_MS || 60000)
  });
  await tts.ttsPromise(String(line.text || ''), output);
  const audioBuffer = await fs.readFile(output);
  if (!audioBuffer.length) throw new Error('Edge TTS returned an empty audio file');
  return { speaker: line.speaker, voice: voiceId, text: line.text, audioBuffer };
}

export async function generateVoice(line, voice, env = process.env) {
  const provider = env.VOICE_PROVIDER || 'edge';
  if (provider === 'mock') return { speaker: line.speaker, voice, text: line.text, audio: null };
  const voiceId = resolveVoice(line, voice, env);
  const output = path.join(os.tmpdir(), `dfre-${randomUUID()}.mp3`);

  if (provider === 'local') return generateLocal(line, voiceId, output.slice(0, -4));
  if (provider !== 'edge') throw new Error(`Unsupported voice provider: ${provider}`);

  const profile = EDGE_PROFILES[voiceId] || { rate: env.EDGE_TTS_RATE || 'default', pitch: env.EDGE_TTS_PITCH || 'default' };
  let lastError;
  for (let attempt = 1; attempt <= 2; attempt++) {
    try {
      console.log(`[TTS] Edge voice ${voiceId} for ${line.speaker} (${profile.rate}, ${profile.pitch})${attempt > 1 ? ` retry ${attempt - 1}` : ''}`);
      const result = await generateEdge(line, voiceId, profile, env, output);
      console.log(`[TTS] Completed ${line.speaker}`);
      return result;
    } catch (error) {
      lastError = error;
      console.warn(`[TTS] ${line.speaker} attempt ${attempt} failed: ${error?.message || error}`);
      if (attempt < 2) await new Promise(resolve => setTimeout(resolve, 1500));
    } finally {
      await fs.rm(output, { force: true }).catch(() => {});
    }
  }
  throw new Error(`TTS failed for ${line.speaker} after 2 attempts: ${lastError?.message || lastError}`);
}
