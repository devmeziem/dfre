import fs from 'node:fs';
import { validateProject } from '../src/schema.mjs';

const file = process.argv[2] ?? 'stories/example.json';
const project = JSON.parse(fs.readFileSync(file, 'utf8'));
validateProject(project);

const total = project.scenes.reduce((sum, scene) => sum + scene.duration, 0);
console.log(JSON.stringify({
  title: project.title,
  aspectRatio: project.aspectRatio ?? '9:16',
  sceneCount: project.scenes.length,
  durationSeconds: total,
  speakers: [...new Set(project.scenes.flatMap(s => s.dialogue.map(d => d.speaker)))]
}, null, 2));
