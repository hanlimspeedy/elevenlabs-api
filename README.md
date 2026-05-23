# ElevenLabs Skills

ElevenLabs developer skills for Claude Code and Codex CLI. Currently ships speech-to-text transcription via Scribe v2.

## Skills

- `elevenlabs-toolkit:speech-to-text` — Batch audio/video transcription (Scribe v2). Includes a Python CLI (`transcribe.py`) and a skill-driven workflow: `.env` check → pre-flight length probe → optional sample testing → auto-saved date-stamped transcript.

## Install

**Claude Code:**

```bash
claude plugin marketplace add hanlimspeedy/elevenlabs-api
claude plugin install elevenlabs-toolkit@elevenlabs-skills
```

**Codex:**

```bash
codex plugin marketplace add hanlimspeedy/elevenlabs-api --ref main
```

Then in Codex, open `/plugins`, install `ElevenLabs Skills > elevenlabs-toolkit`, and start a new thread.

## Use

Trigger the skill by name in a prompt:

```text
speech-to-text 스킬로 meeting.m4a 전사해줘
```

Or just describe the task — Claude/Codex will match the skill from its description.

## Update

**Claude Code:**

```bash
claude plugin marketplace update elevenlabs-skills
```

**Codex:**

```bash
codex plugin marketplace upgrade elevenlabs-skills
```

Start a new session/thread after updating.

Skill or document changes bump version in all four manifests:

- `.claude-plugin/marketplace.json`
- `.agents/plugins/marketplace.json` *(no version field; marketplace catalog only)*
- `plugins/elevenlabs-toolkit/.claude-plugin/plugin.json`
- `plugins/elevenlabs-toolkit/.codex-plugin/plugin.json`

## Validate

```bash
jq . .claude-plugin/marketplace.json
jq . .agents/plugins/marketplace.json
jq . plugins/elevenlabs-toolkit/.claude-plugin/plugin.json
jq . plugins/elevenlabs-toolkit/.codex-plugin/plugin.json
```

Optional Claude Code plugin validation:

```bash
claude plugin validate plugins/elevenlabs-toolkit
```

## Layout

```text
.claude-plugin/marketplace.json                    # Claude marketplace catalog
.agents/plugins/marketplace.json                   # Codex marketplace catalog
.claude/skills/speech-to-text -> ../../plugins/elevenlabs-toolkit/skills/speech-to-text   # dev symlink
.agents/skills/speech-to-text -> ../../plugins/elevenlabs-toolkit/skills/speech-to-text   # dev symlink
plugins/elevenlabs-toolkit/
  .claude-plugin/plugin.json                       # Claude plugin manifest (version)
  .codex-plugin/plugin.json                        # Codex plugin manifest (version)
  skills/
    speech-to-text/                                # source of truth
      SKILL.md
      templates/
        transcribe.py
        requirements.txt
        .env.example
      references/
        transcription-options.md
```

The two top-level symlinks (`.claude/skills/`, `.agents/skills/`) exist so Claude Code and Codex CLI can find the skill when working **inside this repo** without going through the marketplace install flow. External users install via marketplace and never touch these.

**Edit skill content only in `plugins/elevenlabs-toolkit/skills/speech-to-text/`.** Both symlinks resolve to it.

## Standalone use (without plugin install)

`transcribe.py` at the project root is a standalone CLI — works without installing the skill:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env   # then edit .env and paste your ELEVENLABS_API_KEY
.venv/bin/python transcribe.py audio.m4a
```

API key: https://elevenlabs.io/app/developers/api-keys

## License

MIT
