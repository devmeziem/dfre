import fs from 'node:fs';
import { validateProject } from '../src/schema.mjs';

const file = process.argv[2] ?? 'stories/example.json';
const project = JSON.parse(fs.readFileSync(file, 'utf8'));
validateProject(project);
console.log(`Valid project: ${file}`);
