export async function generateStory(input, env = process.env) {
  const provider = env.STORY_PROVIDER || "mock";
  if (provider !== "mock") throw new Error(`Unsupported STORY_PROVIDER: ${provider}`);
  return {
    title: input.title || "The Last Signal",
    genre: input.genre || "mystery",
    durationSeconds: input.durationSeconds || 45,
    scenes: [
      { id: "s1", duration: 7, location: "quiet apartment at night", visual: "young inventor notices a strange blue signal outside", dialogue: [{ speaker: "narrator", text: "At midnight, the signal appeared again." }] },
      { id: "s2", duration: 8, location: "rooftop overlooking the city", visual: "inventor follows the signal to the rooftop and sees lights forming a message", dialogue: [{ speaker: "mira", text: "That message... it knows my name." }] }
    ]
  };
}
