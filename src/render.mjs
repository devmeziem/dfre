import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import fs from 'node:fs/promises';
import path from 'node:path';
const exec = promisify(execFile);

async function runFfmpeg(args) { await exec('ffmpeg', ['-y', '-hide_banner', '-loglevel', 'error', ...args]); }

export async function renderVideo(plan, assets, output = 'output/final.mp4') {
  await fs.mkdir(path.dirname(output), { recursive: true });
  const work = path.join(path.dirname(output), 'render');
  await fs.mkdir(work, { recursive: true });
  const clips = [];
  for (const asset of assets) {
    if (!asset.imagePath) throw new Error(`Missing image for ${asset.sceneId}`);
    const audio = asset.voices?.filter(v => v.audioPath).map(v => v.audioPath) || [];
    let audioPath = null;
    if (audio.length === 1) audioPath = audio[0];
    if (audio.length > 1) {
      const list = path.join(work, `${asset.sceneId}-audio.txt`);
      await fs.writeFile(list, audio.map(p => `file '${path.resolve(p).replaceAll("'", "'\\''")}'`).join('\n'));
      audioPath = path.join(work, `${asset.sceneId}-audio.mp3`);
      await runFfmpeg(['-f', 'concat', '-safe', '0', '-i', list, '-c:a', 'libmp3lame', audioPath]);
    }
    const clip = path.join(work, `${asset.sceneId}.mp4`);
    const args = ['-loop', '1', '-i', asset.imagePath];
    if (audioPath) args.push('-i', audioPath);
    args.push('-t', String(asset.duration), '-vf', 'scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2', '-r', '30', '-c:v', 'libx264', '-pix_fmt', 'yuv420p');
    if (audioPath) args.push('-c:a', 'aac', '-shortest'); else args.push('-an');
    args.push(clip);
    await runFfmpeg(args);
    clips.push(clip);
  }
  const concat = path.join(work, 'concat.txt');
  await fs.writeFile(concat, clips.map(p => `file '${path.resolve(p).replaceAll("'", "'\\''")}'`).join('\n'));
  await runFfmpeg(['-f', 'concat', '-safe', '0', '-i', concat, '-c', 'copy', output]);
  return output;
}
