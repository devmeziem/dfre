const NON_CHARACTER_SPEAKERS = new Set(['narrator', 'radio voice', 'radio', 'announcer', 'voice over', 'voiceover', 'system', 'ai']);

export function validateProject(project) {
  if (!project || typeof project !== 'object') throw new Error('Project must be an object');
  if (!project.title) throw new Error('Missing title');
  if (!Array.isArray(project.scenes) || project.scenes.length === 0) throw new Error('Project must contain at least one scene');

  const characters = Array.isArray(project.characters) ? project.characters : [];
  const characterNames = new Set(characters.map((c) => String(c?.name || '').trim().toLowerCase()).filter(Boolean));
  if (characters.length > 0 && characters.length < 2) throw new Error('Project must contain at least 2 characters when characters are provided');

  let totalDuration = 0;
  for (const [index, scene] of project.scenes.entries()) {
    if (!scene.id) throw new Error(`Scene ${index + 1}: missing id`);
    if (!Number.isFinite(Number(scene.duration)) || Number(scene.duration) <= 0) throw new Error(`Scene ${index + 1}: invalid duration`);
    if (!scene.imagePrompt) throw new Error(`Scene ${index + 1}: missing imagePrompt`);
    if (!Array.isArray(scene.dialogue)) throw new Error(`Scene ${index + 1}: dialogue must be an array`);
    totalDuration += Number(scene.duration);

    for (const [lineIndex, line] of scene.dialogue.entries()) {
      if (!line?.speaker || !String(line.speaker).trim()) throw new Error(`Scene ${index + 1}, dialogue ${lineIndex + 1}: missing speaker`);
      if (!line?.text || !String(line.text).trim()) throw new Error(`Scene ${index + 1}, dialogue ${lineIndex + 1}: missing text`);
      const speaker = String(line.speaker).trim().toLowerCase();
      if (characterNames.size && !characterNames.has(speaker) && !NON_CHARACTER_SPEAKERS.has(speaker)) {
        throw new Error(`Scene ${index + 1}, dialogue ${lineIndex + 1}: unknown character "${line.speaker}"`);
      }
    }
  }

  if (totalDuration > 120) throw new Error(`Project duration ${totalDuration}s exceeds the 120-second limit`);
  return true;
}
