import fs from 'node:fs';
import { validateProject } from '../src/schema.mjs';

const file = process.argv[2] ?? 'stories/example.json';
const project = JSON.parse(fs.readFileSync(file, 'utf8'));
validateProject(project);

const totalDuration = project.scenes.reduce((sum, scene) => sum + Number(scene.duration || 0), 0);
if (!Number.isFinite(totalDuration) || totalDuration <= 0) throw new Error('Project has invalid total duration');
if (totalDuration > 120) throw new Error('Project exceeds the 120-second short-film limit');

for (const [index, scene] of project.scenes.entries()) {
  if (scene.duration < 1 || scene.duration > 30) throw new Error(`Scene ${index + 1}: duration must be between 1 and 30 seconds`);
  for (const [lineIndex, line] of scene.dialogue.entries()) {
    if (!line.speaker || !String(line.speaker).trim()) throw new Error(`Scene ${index + 1}, dialogue ${lineIndex + 1}: missing speaker`);
    if (!line.text || !String(line.text).trim()) throw new Error(`Scene ${index + 1}, dialogue ${lineIndex + 1}: missing text`);
  }
}

console.log(`Valid project: ${file} (${project.scenes.length} scenes, ${totalDuration}s)`);
