# dfre

A modular media-generation pipeline for short-form projects.

## V1
- Generate original stories and scripts
- Break stories into scenes
- Define recurring characters
- Generate scene images through a provider adapter
- Generate separate voices for characters and narration
- Build timed captions
- Assemble a vertical 9:16 MP4

The system is provider-independent so image, voice, and story services can be replaced later.

## Planned flow
`idea -> story -> scenes -> images -> voices -> captions -> render`

## Development
V1 is designed to run locally or in CI. Provider credentials are supplied through environment variables/secrets and are never committed to the repository.
