# Codex HUD

Windows-friendly sidecar HUD for local Codex sessions.

## Included files

- `scripts/codex_hud.py` - main HUD program
- `scripts/codex_hud.ps1` - PowerShell wrapper
- `scripts/codex_hud.bat` - Batch wrapper

## What it shows

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

## Notes

This is a sidecar HUD, not a native Codex statusline plugin. It reads local session JSONL files under `~/.codex/sessions`.

Current Codex local logs expose the context window size, but not a reliable real-time context occupancy percentage.

Default layout is `compact` to mimic a Claude-HUD-style 1 to 2 line display.

`single` is the tightest mode when you want a statusline-like one-row view.

`codex_hud.bat` defaults to `--layout single --watch` when you do not pass any arguments.
