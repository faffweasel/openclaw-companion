---
name: multi-provider
description: Route LLM text generation to different providers and models. Used by dreaming (reflection), and available to any skill that needs model-specific generation. Supports Venice and OpenRouter.
metadata: '{"nanobot":{"emoji":"🔀","requires":{"bins":["python3"],"env":["OPENROUTER_API_KEY"]}}}'
---

# Multi-Provider

Route text generation to specific provider/model combinations. Called by other skills that need model-specific generation (e.g. dreaming uses heretic for creative content, opus for deep reflection).

## Setup

API keys are passed via `docker-compose.override.yml` — see `docs/setup-reference.md` for configuration. At least one provider key is required (unless using a local provider like Ollama that needs no key).

### Provider Registry

The wizard copies `seed/providers.json` to `skills-data/multi-provider/providers.json`. This file defines all available providers:

```json
{
  "providers": {
    "openrouter": {
      "endpoint": "https://openrouter.ai/api/v1/chat/completions",
      "apiKeyEnvVar": "OPENROUTER_API_KEY",
      "format": "openai"
    },
    "ollama": {
      "endpoint": "http://localhost:11434/v1/chat/completions",
      "apiKeyEnvVar": "",
      "format": "openai"
    }
  }
}
```

Add, remove, or edit providers by editing this file. Any OpenAI-compatible endpoint works. Set `apiKeyEnvVar` to empty string for providers that need no key (Ollama, local vLLM).

Check provider status: `python3 skills/multi-provider/scripts/providers.py --list-providers`

## Usage

### CLI

```bash
python3 skills/multi-provider/scripts/providers.py \
  --provider openrouter \
  --model google/gemini-2.5-flash \
  --system "You are a helpful assistant." \
  --prompt "Explain quantum computing in one paragraph."
```

Output: generated text to stdout. Errors to stderr.

### Flags

| Flag | Required | Description |
|---|---|---|
| `--provider` | Yes | `openrouter` or `venice` |
| `--model` | Yes | Model ID (provider-specific) |
| `--prompt` | Yes | User message |
| `--system` | No | System prompt (default: none) |
| `--max-tokens` | No | Max response tokens (default: 2048) |
| `--temperature` | No | Temperature 0.0-2.0 (default: provider default) |
| `--no-identity` | No | Skip identity context (see below) |

### From other scripts

```bash
RESULT=$(python3 "$SKILLS_DIR/multi-provider/scripts/providers.py" \
  --provider venice --model heretic-r1 \
  --system "Dream freely." --prompt "Explore this topic...")
```

## Identity Context

By default, `providers.py` reads SOUL.md, IDENTITY.md, and USER.md from the workspace root and prepends them to the system prompt. This ensures the target model has the companion's full personality.

Use `--no-identity` for calls that shouldn't have personality context (e.g. generic utility tasks, structured data extraction).

## Supported Providers

| Provider | API Key Env Var | Endpoint |
|---|---|---|
| openrouter | `OPENROUTER_API_KEY` | `https://openrouter.ai/api/v1/chat/completions` |
| venice | `VENICE_API_KEY` | `https://api.venice.ai/api/v1/chat/completions` |

Both use OpenAI-compatible chat completion format. Adding a new provider is adding an entry to the `PROVIDERS` dict in `providers.py`.

## Troubleshooting

**"No API key found for provider X"** — See `docs/setup-reference.md` for Docker environment configuration. Restart with `docker compose up -d` after changes.

**"Unknown provider"** — Only `openrouter` and `venice` are supported. Check spelling.
