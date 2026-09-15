import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import fs from 'node:fs/promises';
import path from 'node:path';
const exec = promisify(execFile);

async function runFfmpeg(args) {
  await exec('ffmpeg', ['-y', '-hide_banner', '-loglevel', 'error', ...args]);
}

function assTime(sec) {
  const cs = Math.max(0, Math.round((Number(sec) || 0) * 100));
  const h = Math.floor(cs / 360000);
  const m = Math.floor((cs % 360000) / 6000);
  const s = Math.floor((cs % 6000) / 100);
  const c = cs % 100;
  return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}.${String(c).padStart(2, '0')}`;
}

function filterPath(p) {
  return path.resolve(p).replaceAll('\\', '/').replaceAll(':', '\\:').replaceAll("'", "\\'");
}

function escapeAssText(text) {
  return String(text || '').replace(/\r?\n/g, ' ').replace(/[{}]/g, '').replace(/\\/g, '').trim();
}

// Hi-style mobile captions: compact 5-word groups, uppercase, with real ASS karaoke timing.
function buildAss(lines, duration) {
  const safeLines = lines.map(v => ({ text: escapeAssText(v.text).toUpperCase(), duration: Number(v.duration) || 0 })).filter(v => v.text);
  if (!safeLines.length) return '';
  const hinted = safeLines.reduce((n, v) => n + v.duration, 0);
  const scale = hinted > 0 ? duration / hinted : 1;
  let current = 0;
  const events = [];

  for (const line of safeLines) {
    const words = line.text.split(/\s+/).filter(Boolean);
    if (!words.length) continue;
    const lineDuration = line.duration > 0 ? line.duration * scale : duration / safeLines.length;
    const lineEnd = Math.min(duration, current + lineDuration);

    // Keep each caption to at most 5 words so it stays clean inside the rounded card.
    for (let start = 0; start < words.length; start += 5) {
      const chunk = words.slice(start, start + 5);
      const chunkWordCount = chunk.length;
      const chunkStartRatio = start / words.length;
      const chunkEndRatio = (start + chunkWordCount) / words.length;
      const chunkStart = current + (lineEnd - current) * chunkStartRatio;
      const chunkEnd = current + (lineEnd - current) * chunkEndRatio;
      const totalCs = Math.max(1, Math.round((chunkEnd - chunkStart) * 100));
      const baseCs = Math.max(1, Math.floor(totalCs / chunkWordCount));
      let used = 0;
      const karaoke = chunk.map((word, i) => {
        const cs = i === chunkWordCount - 1 ? Math.max(1, totalCs - used) : baseCs;
        used += cs;
        // ASS karaoke tags MUST be inside override braces, e.g. {\\kf38}WORD.
        return `{\\kf${cs}}${word}`;
      }).join(' ');
      events.push(`Dialogue: 0,${assTime(chunkStart)},${assTime(chunkEnd)},Caption,,0,0,0,,${karaoke}`);
    }
    current = lineEnd;
  }

  return `[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nScaledBorderAndShadow: yes\n\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Caption,DejaVu Sans,54,&H00FFFFFF,&H00D0D0D0,&H00101010,&H00000000,-1,0,0,0,100,100,0,0,1,3,1,2,80,80,175,1\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n${events.join('\n')}\n`;
}

async function makeRoundedCaptionCard(work) {
  const card = path.join(work, 'caption-card.svg');
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="940" height="250" viewBox="0 0 940 250"><rect x="2" y="2" width="936" height="246" rx="38" ry="38" fill="#050505" fill-opacity="0.82" stroke="#ffffff" stroke-opacity="0.08" stroke-width="4"/></svg>`;
  await fs.writeFile(card, svg, 'utf8');
  return card;
}

export async function renderVideo(plan, assets, output = 'output/final.mp4') {
  await fs.mkdir(path.dirname(output), { recursive: true });
  const work = path.join(path.dirname(output), 'render');
  await fs.mkdir(work, { recursive: true });
  const clips = [];
  const captionCard = await makeRoundedCaptionCard(work);

  for (const asset of assets) {
    if (!asset.imagePath) throw new Error(`Missing image for ${asset.sceneId}`);
    const lines = asset.voices || [];
    const ass = path.join(work, `${asset.sceneId}.ass`);
    await fs.writeFile(ass, buildAss(lines, asset.duration), 'utf8');

    const audio = lines.filter(v => v.audioPath).map(v => v.audioPath);
    let audioPath = null;
    if (audio.length === 1) audioPath = audio[0];
    if (audio.length > 1) {
      const list = path.join(work, `${asset.sceneId}-audio.txt`);
      await fs.writeFile(list, audio.map(p => `file '${path.resolve(p).replaceAll("'", "'\\''")}'`).join('\n'));
      audioPath = path.join(work, `${asset.sceneId}-audio.mp3`);
      await runFfmpeg(['-f', 'concat', '-safe', '0', '-i', list, '-c:a', 'libmp3lame', '-b:a', '128k', audioPath]);
    }

    const clip = path.join(work, `${asset.sceneId}.mp4`);
    const duration = Number(asset.duration) || 1;
    // Lightweight Hi-inspired motion treatment: slow push-in, subtle contrast/saturation,
    // vignette and short fades. It animates the still image without generating extra images.
    const motion = `scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,zoompan=z='min(zoom+0.0007,1.08)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=30,eq=contrast=1.04:saturation=1.04,vignette=PI/5,fade=t=in:st=0:d=0.18,fade=t=out:st=${Math.max(0.2, duration - 0.22)}:d=0.22`;
    const assFilter = `subtitles='${filterPath(ass)}'`;
    const filterComplex = `[0:v]${motion}[scene];[scene][1:v]overlay=x=70:y=1605:format=auto:shortest=1[carded];[carded]${assFilter}[vout]`;

    const args = ['-loop', '1', '-i', asset.imagePath, '-loop', '1', '-i', captionCard];
    if (audioPath) args.push('-i', audioPath);
    args.push('-t', String(duration), '-filter_complex', filterComplex, '-map', '[vout]');
    if (audioPath) args.push('-map', '2:a?', '-c:a', 'aac', '-b:a', '128k', '-ar', '44100', '-shortest');
    args.push('-r', '30', '-c:v', 'libx264', '-preset', 'veryfast', '-pix_fmt', 'yuv420p', clip);
    await runFfmpeg(args);
    clips.push(clip);
  }

  if (!clips.length) throw new Error('No scenes to render');
  const concat = path.join(work, 'concat.txt');
  await fs.writeFile(concat, clips.map(p => `file '${path.resolve(p).replaceAll("'", "'\\''")}'`).join('\n'));
  await runFfmpeg(['-f', 'concat', '-safe', '0', '-i', concat, '-c', 'copy', output]);
  return output;
}
