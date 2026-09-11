# dfre

A modular media-generation pipeline for short-form projects.

## V1 pipeline
`idea -> story -> scenes -> images -> voices -> captions -> 9:16 MP4`

The project supports original multi-scene stories, recurring characters, separate character/narrator voices, timed burned-in captions, and 1080x1920 video output. Provider adapters keep the generation services replaceable.

## GitHub Actions
Run **Actions → build → Run workflow** and enter an optional story, genre, and duration. The finished `final.mp4` is uploaded as the `final-video` artifact.

Add these repository secrets before using the real providers:
- `OPENROUTER_API_KEY`
- `HF_TOKEN`
- `ELEVENLABS_API_KEY`
- `ELEVENLABS_VOICE_ID` (fallback voice)
- `VOICE_NARRATOR` and any `VOICE_<SPEAKER>` values used by stories

Optional model secrets: `STORY_MODEL`, `IMAGE_MODEL`, `ELEVENLABS_MODEL`.

The default demo provider is mock; real CI runs select the real providers through environment variables. Never commit API keys or generated credentials.
