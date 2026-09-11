import fs from 'node:fs/promises';
import { buildPlan, prepareAssets } from '../src/pipeline.mjs';

const input = process.argv[2] || 'stories/demo.json';
const plan = await buildPlan(input);
await fs.writeFile('stories/plan.json', JSON.stringify(plan, null, 2));
await prepareAssets(plan, 'output/assets');
console.log(`Prepared ${plan.scenes.length} scene(s).`);
console.log('V1 render stage is provider-ready; real media adapters can now be plugged in.');
