---
name: codex-hud
description: Use when the user wants a live sidecar HUD for local Codex sessions on Windows, including session activity, rate limits, recent agent messages, and single-line, compact, or expanded status views.
---

# Codex HUD

Use the bundled HUD instead of rebuilding one from scratch.

## When to use

- The user wants a Claude-HUD-style display for Codex.
- The user wants to monitor local Codex session activity, rate limits, or recent agent messages.
- The user wants a compact terminal summary of the latest local Codex session.

## Run

Default single-line watch mode on Windows:

```bat
scripts\codex_hud.bat
```

PowerShell wrapper:

```powershell
.\scripts\codex_hud.ps1 --watch
```

Python entrypoint:

```powershell
python scripts/codex_hud.py --layout single --watch
```

Other useful variants:

```powershell
python scripts/codex_hud.py --layout compact --watch
python scripts/codex_hud.py --layout expanded
python scripts/codex_hud.py --layout single --no-color
```

## Notes

- Reads local session JSONL files from `~/.codex/sessions`.
- Shows context window size, but not a reliable real-time context occupancy percentage, because the local session logs do not expose it.
- Prefer `single` for a statusline-like one-row view, `compact` for a two-line HUD, and `expanded` for debugging.
