import fs from 'node:fs/promises';
import { buildPlan, prepareAssets } from '../src/pipeline.mjs';
import { renderVideo } from '../src/render.mjs';

const input = process.argv[2] || 'stories/demo.json';
const plan = await buildPlan(input);
await fs.writeFile('stories/plan.json', JSON.stringify(plan, null, 2));
const assets = await prepareAssets(plan, 'output/assets');
const output = await renderVideo(plan, assets, 'output/final.mp4');
console.log(`Rendered ${plan.scenes.length} scene(s) to ${output}`);
