import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import fs from 'node:fs/promises';
import path from 'node:path';
const exec = promisify(execFile);
async function runFfmpeg(args) { await exec('ffmpeg', ['-y', '-hide_banner', '-loglevel', 'error', ...args]); }
function stamp(sec) { const ms = Math.max(0, Math.round(sec * 1000)); const h = Math.floor(ms / 3600000); const m = Math.floor((ms % 3600000) / 60000); const s = Math.floor((ms % 60000) / 1000); const x = ms % 1000; return `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')},${String(x).padStart(3,'0')}`; }
function filterPath(p) { return path.resolve(p).replaceAll('\\','/').replaceAll(':','\\:').replaceAll("'","\\'"); }
export async function renderVideo(plan, assets, output = 'output/final.mp4') {
  await fs.mkdir(path.dirname(output), { recursive: true });
  const work = path.join(path.dirname(output), 'render');
  await fs.mkdir(work, { recursive: true });
  const clips = [];
  for (const asset of assets) {
    if (!asset.imagePath) throw new Error(`Missing image for ${asset.sceneId}`);
    const srt = path.join(work, `${asset.sceneId}.srt`);
    const lines = asset.voices || [];
    const each = lines.length ? asset.duration / lines.length : asset.duration;
    await fs.writeFile(srt, lines.map((v,i) => `${i+1}\n${stamp(i*each)} --> ${stamp(Math.min(asset.duration,(i+1)*each))}\n${v.text}\n`).join('\n'));
    const audio = asset.voices?.filter(v => v.audioPath).map(v => v.audioPath) || [];
    let audioPath = null;
    if (audio.length === 1) audioPath = audio[0];
    if (audio.length > 1) {
      const list = path.join(work, `${asset.sceneId}-audio.txt`);
      await fs.writeFile(list, audio.map(p => `file '${path.resolve(p).replaceAll("'", "'\\''")}'`).join('\n'));
      audioPath = path.join(work, `${asset.sceneId}-audio.mp3`);
      await runFfmpeg(['-f','concat','-safe','0','-i',list,'-c:a','libmp3lame',audioPath]);
    }
    const clip = path.join(work, `${asset.sceneId}.mp4`);
    const subtitleStyle = 'FontSize=22,Outline=2,Shadow=1,MarginV=80,Alignment=2,BorderStyle=1';
    const vf = `scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,subtitles='${filterPath(srt)}':force_style='${subtitleStyle}'`;
    const args = ['-loop','1','-i',asset.imagePath];
    if (audioPath) args.push('-i',audioPath);
    args.push('-t',String(asset.duration),'-vf',vf,'-r','30','-c:v','libx264','-pix_fmt','yuv420p');
    if (audioPath) args.push('-c:a','aac'); else args.push('-an');
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
