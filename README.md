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


## Crypto opportunity Telegram digest

The **Crypto Opportunity Telegram Digest** workflow runs daily at 09:00 UTC and can also be started from **Actions → Crypto Opportunity Telegram Digest → Run workflow**. It reads public RSS/Atom feeds, filters for crypto/web3 opportunities with bounty, grant, hackathon, prize, reward, paid, or funding language, and posts up to 10 recent matches. It does not pad the channel when fewer matches are found.

Add these repository **Actions secrets**:
- `TELEGRAM_BOT_TOKEN` — token from BotFather
- `TELEGRAM_CHANNEL_ID` — channel ID (for a public channel, this can be `@channelusername`); add the bot to the channel with permission to post

Optional repository **Actions variable**:
- `CRYPTO_OPPORTUNITY_FEEDS` — newline- or comma-separated RSS/Atom feed URLs. Defaults are Gitcoin's blog feed and DoraHacks' blog feed. The workflow uses only public feeds and does not need a separate API key.

The feed filter is heuristic, so review posted opportunities and verify eligibility, deadlines, and payment terms on the source page. It never guarantees that an opportunity pays.
