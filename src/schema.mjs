export function validateProject(project) {
  if (!project || typeof project !== 'object') throw new Error('Project must be an object');
  if (!project.title) throw new Error('Missing title');
  if (!Array.isArray(project.scenes) || project.scenes.length === 0) {
    throw new Error('Project must contain at least one scene');
  }

  for (const [index, scene] of project.scenes.entries()) {
    if (!scene.id) throw new Error(`Scene ${index + 1}: missing id`);
    if (!scene.duration || scene.duration <= 0) throw new Error(`Scene ${index + 1}: invalid duration`);
    if (!scene.imagePrompt) throw new Error(`Scene ${index + 1}: missing imagePrompt`);
    if (!Array.isArray(scene.dialogue)) throw new Error(`Scene ${index + 1}: dialogue must be an array`);
  }

  return true;
}
