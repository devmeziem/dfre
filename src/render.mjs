import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import fs from 'node:fs/promises';
import path from 'node:path';
const exec = promisify(execFile);
async function runFfmpeg(args) { await exec('ffmpeg', ['-y', '-hide_banner', '-loglevel', 'error', ...args]); }
function stamp(sec) { const ms = Math.max(0, Math.round(sec * 1000)); const h = Math.floor(ms / 3600000); const m = Math.floor((ms % 3600000) / 60000); const s = Math.floor((ms % 60000) / 1000); const x = ms % 1000; return `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')},${String(x).padStart(3,'0')}`; }
function filterPath(p) { return path.resolve(p).replaceAll('\\','/').replaceAll(':','\\:').replaceAll("'","\\'"); }
function escapeSrtText(text) { return String(text || '').replace(/\r?\n/g, ' ').trim(); }

function buildSrt(lines, duration) {
  if (!lines.length) return '';
  const words = lines.flatMap((line) => escapeSrtText(line.text).split(/\s+/).filter(Boolean));
  if (!words.length) return '';
  const chunkSize = 5;
  const timePerWord = duration / words.length;
  let out = '';
  let counter = 1;
  for (let i = 0; i < words.length; i += chunkSize) {
    const chunk = words.slice(i, i + chunkSize).join(' ').toUpperCase();
    const start = i * timePerWord;
    const end = Math.min(duration, (i + Math.min(chunkSize, words.length - i)) * timePerWord);
    out += `${counter}\n${stamp(start)} --> ${stamp(end)}\n${chunk}\n\n`;
    counter++;
  }
  return out;
}

export async function renderVideo(plan, assets, output = 'output/final.mp4') {
  await fs.mkdir(path.dirname(output), { recursive: true });
  const work = path.join(path.dirname(output), 'render');
  await fs.mkdir(work, { recursive: true });
  const clips = [];
  for (const asset of assets) {
    if (!asset.imagePath) throw new Error(`Missing image for ${asset.sceneId}`);
    const srt = path.join(work, `${asset.sceneId}.srt`);
    const lines = asset.voices || [];
    await fs.writeFile(srt, buildSrt(lines, asset.duration));

    const audio = lines.filter(v => v.audioPath).map(v => v.audioPath);
    let audioPath = null;
    if (audio.length === 1) audioPath = audio[0];
    if (audio.length > 1) {
      const list = path.join(work, `${asset.sceneId}-audio.txt`);
      await fs.writeFile(list, audio.map(p => `file '${path.resolve(p).replaceAll("'", "'\\''")}'`).join('\n'));
      audioPath = path.join(work, `${asset.sceneId}-audio.mp3`);
      await runFfmpeg(['-f','concat','-safe','0','-i',list,'-c:a','libmp3lame','-b:a','128k',audioPath]);
    }

    const clip = path.join(work, `${asset.sceneId}.mp4`);
    // Inspired by Hi's mobile cartoon factory: 1080x1920 vertical composition,
    // crisp punchy 5-word caption chunks, and subtle continuous camera motion.
    const subtitleStyle = 'FontName=DejaVu Sans,FontSize=22,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=1,Alignment=2,MarginV=80';
    const vf = `scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,zoompan=z='min(zoom+0.0007,1.08)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=30,subtitles='${filterPath(srt)}':force_style='${subtitleStyle}'`;
    const args = ['-loop','1','-i',asset.imagePath];
    if (audioPath) args.push('-i',audioPath);
    args.push('-t',String(asset.duration),'-vf',vf,'-r','30','-c:v','libx264','-preset','veryfast','-pix_fmt','yuv420p');
    if (audioPath) args.push('-c:a','aac','-b:a','128k','-ar','44100','-shortest'); else args.push('-an');
    args.push(clip);
    await runFfmpeg(args);
    clips.push(clip);
  }
  if (!clips.length) throw new Error('No scenes to render');
  const concat = path.join(work,'concat.txt');
  await fs.writeFile(concat, clips.map(p => `file '${path.resolve(p).replaceAll("'", "'\\''")}'`).join('\n'));
  await runFfmpeg(['-f','concat','-safe','0','-i',concat,'-c','copy',output]);
  return output;
}
