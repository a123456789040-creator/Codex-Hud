# Codex HUD

Windows-friendly sidecar HUD and Codex skill/plugin source for local Codex sessions.

## Repo layout

- `.codex-plugin/plugin.json` - Codex plugin manifest
- `.app.json` - app manifest placeholder for Codex plugin wiring
- `.agents/plugins/marketplace.json` - repo-local marketplace entry for this plugin
- `skills/codex-hud/SKILL.md` - Codex skill trigger and run guide
- `scripts/codex_hud.py` - main HUD program
- `scripts/codex_hud.ps1` - PowerShell wrapper
- `scripts/codex_hud.bat` - Batch wrapper

## What it does

- single-line, compact 2-line, or expanded full view
- latest active session file
- working directory, session id, CLI version, source
- context window size
- primary and secondary rate-limit percentages
- last agent phase and last agent message
- recent event timeline and event counts

## Requirements

- Windows PowerShell or Command Prompt
- Python 3.11+
- Local Codex sessions under `~/.codex/sessions`

## Install

### 1. Clone the repo locally

```powershell
git clone https://github.com/a123456789040-creator/Codex-Hud.git $env:USERPROFILE\.codex\plugins\codex-hud
```

### 2. Expose the skill to Codex

```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.agents\skills" | Out-Null
cmd /c mklink /J "$env:USERPROFILE\.agents\skills\codex-hud" "$env:USERPROFILE\.codex\plugins\codex-hud\skills\codex-hud"
```

### 3. Restart Codex

Codex discovers skills at startup.

## Run

Default compact HUD:

```powershell
python scripts/codex_hud.py
```

Single-line ultra-compact view:

```powershell
python scripts/codex_hud.py --layout single
```

Expanded view:

```powershell
python scripts/codex_hud.py --layout expanded
```

Watch mode:

```powershell
python scripts/codex_hud.py --watch
```

PowerShell wrapper:

```powershell
.\scripts\codex_hud.ps1 --watch
```

Batch wrapper:

```bat
scripts\codex_hud.bat
```

Batch wrapper with custom layout:

```bat
scripts\codex_hud.bat --layout compact --watch --no-color
```

Disable ANSI color:

```powershell
python scripts/codex_hud.py --layout single --no-color
```

## Repo-local marketplace

This repo includes `.agents/plugins/marketplace.json` as a one-plugin local marketplace definition.

In this repo, the marketplace entry points to `./` because the plugin lives at the repository root. If you vendor this plugin into a larger marketplace under `plugins/codex-hud`, change the marketplace `source.path` to `./plugins/codex-hud`.

## Notes

This is a sidecar HUD, not a native Codex statusline plugin. It reads local session JSONL files under `~/.codex/sessions`.

Current Codex local logs expose the context window size, but not a reliable real-time context occupancy percentage.

Default layout is `compact` to mimic a Claude-HUD-style 1 to 2 line display.

`single` is the tightest mode when you want a statusline-like one-row view.

`codex_hud.bat` defaults to `--layout single --watch` when you do not pass any arguments.
