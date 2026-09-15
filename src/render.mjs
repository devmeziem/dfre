import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import fs from 'node:fs/promises';
import path from 'node:path';
const exec = promisify(execFile);

async function runFfmpeg(args) {
  await exec('ffmpeg', ['-y', '-hide_banner', '-loglevel', 'error', ...args]);
}

function assTime(sec) {
  const safe = Math.max(0, Number(sec) || 0);
  const cs = Math.round(safe * 100);
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
  return String(text || '')
    .replace(/\r?\n/g, ' ')
    .replace(/[{}]/g, '')
    .replace(/\\/g, '')
    .trim();
}

// Hi-style mobile captions: short word groups with true karaoke timing.
function buildAss(lines, duration) {
  const safeLines = lines
    .map(v => ({ text: escapeAssText(v.text), duration: Number(v.duration) || 0 }))
    .filter(v => v.text);
  if (!safeLines.length) return '';

  const totalLineHint = safeLines.reduce((n, v) => n + v.duration, 0);
  const scale = totalLineHint > 0 ? duration / totalLineHint : 1;
  let current = 0;
  const events = [];

  for (const line of safeLines) {
    const words = line.text.split(/\s+/).filter(Boolean);
    if (!words.length) continue;
    const lineDuration = line.duration > 0 ? line.duration * scale : duration / safeLines.length;
    const wordCs = Math.max(1, Math.round((lineDuration * 100) / words.length));
    const actualLineEnd = Math.min(duration, current + lineDuration);
    const karaoke = words.map((word, i) => `\\k${i === words.length - 1 ? Math.max(1, Math.round((actualLineEnd - current) * 100) - wordCs * (words.length - 1)) : wordCs}${word}`).join(' ');
    events.push(`Dialogue: 0,${assTime(current)},${assTime(actualLineEnd)},Caption,,0,0,0,,${karaoke}`);
    current = actualLineEnd;
  }

  return `[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nScaledBorderAndShadow: yes\n\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Caption,DejaVu Sans,54,&H00FFFFFF,&H00B8B8B8,&H00101010,&H00000000,-1,0,0,0,100,100,0,0,1,3,1,2,80,80,205,1\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n${events.join('\n')}\n`;
}

async function makeRoundedCaptionCard(work) {
  const card = path.join(work, 'caption-card.png');
  try {
    await exec('python3', [path.join(process.cwd(), 'scripts', 'make_caption_card.py'), card]);
    return card;
  } catch (err) {
    console.warn(`[Render] Caption card generation failed; continuing without card: ${err.message}`);
    return null;
  }
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
    // Hi-inspired visual treatment: slow cinematic push-in, subtle contrast/vignette,
    // vertical 9:16 composition, gentle fades, then karaoke captions over a rounded card.
    const base = `scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,zoompan=z='min(zoom+0.0007,1.08)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=30,eq=contrast=1.04:saturation=1.04,vignette=PI/5,fade=t=in:st=0:d=0.18,fade=t=out:st=${Math.max(0.2, Number(asset.duration) - 0.22)}:d=0.22`;
    const subtitleFilter = `subtitles='${filterPath(ass)}'`;
    const filters = captionCard
      ? `[0:v]${base}[scene];[scene][1:v]overlay=x=70:y=1605:format=auto:shortest=1[carded];[carded]${subtitleFilter}`
      : `${base},${subtitleFilter}`;

    const args = ['-loop', '1', '-i', asset.imagePath];
    if (captionCard) args.push('-loop', '1', '-i', captionCard);
    if (audioPath) args.push('-i', audioPath);
    args.push('-t', String(asset.duration), '-filter_complex', filters, '-r', '30', '-c:v', 'libx264', '-preset', 'veryfast', '-pix_fmt', 'yuv420p');
    if (audioPath) {
      const audioIndex = captionCard ? 2 : 1;
      args.push('-map', '[vout]', '-map', `${audioIndex}:a?`, '-c:a', 'aac', '-b:a', '128k', '-ar', '44100', '-shortest');
    } else {
      args.push('-map', '0:v');
    }
    // Give the final video a deterministic filtered output label when audio is present.
    if (audioPath) {
      args[args.indexOf('-filter_complex') + 1] += ';[outv]null[vout]';
    }
    args.push(clip);

    // The first command uses [outv] only when audio is present; rebuild cleanly to avoid
    // relying on implicit filter labels.
    const filterComplex = captionCard
      ? `[0:v]${base}[scene];[scene][1:v]overlay=x=70:y=1605:format=auto:shortest=1[carded];[carded]${subtitleFilter}[vout]`
      : `[0:v]${base},${subtitleFilter}[vout]`;
    const filterArgs = args.slice(0, args.indexOf('-filter_complex') + 1);
    filterArgs.push(filterComplex, '-r', '30', '-c:v', 'libx264', '-preset', 'veryfast', '-pix_fmt', 'yuv420p');
    if (audioPath) {
      const audioIndex = captionCard ? 2 : 1;
      filterArgs.push('-map', '[vout]', '-map', `${audioIndex}:a?`, '-c:a', 'aac', '-b:a', '128k', '-ar', '44100', '-shortest');
    } else {
      filterArgs.push('-map', '[vout]');
    }
    filterArgs.push(clip);

    await runFfmpeg(filterArgs);
    clips.push(clip);
  }

  if (!clips.length) throw new Error('No scenes to render');
  const concat = path.join(work, 'concat.txt');
  await fs.writeFile(concat, clips.map(p => `file '${path.resolve(p).replaceAll("'", "'\\''")}'`).join('\n'));
  await runFfmpeg(['-f', 'concat', '-safe', '0', '-i', concat, '-c', 'copy', output]);
  return output;
}
