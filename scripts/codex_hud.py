from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SESSION_ROOT = Path.home() / ".codex" / "sessions"
RESET = "\033[0m"
COLORS = {
    "dim": "\033[2m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
    "bright_black": "\033[90m",
    "bright_red": "\033[91m",
    "bright_green": "\033[92m",
    "bright_yellow": "\033[93m",
    "bright_blue": "\033[94m",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prototype HUD for Codex sessions on Windows."
    )
    parser.add_argument(
        "--session",
        type=Path,
        help="Specific Codex session JSONL file to inspect.",
    )
    parser.add_argument(
        "--sessions-root",
        type=Path,
        default=SESSION_ROOT,
        help="Root directory containing Codex session JSONL files.",
    )
    parser.add_argument(
        "--layout",
        choices=("single", "compact", "expanded"),
        default="compact",
        help="Display layout style.",
    )
    parser.add_argument(
        "--path-levels",
        type=int,
        default=2,
        help="How many trailing path segments to show in compact mode.",
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Refresh the display continuously.",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Refresh interval in seconds for watch mode.",
    )
    parser.add_argument(
        "--tail-events",
        type=int,
        default=6,
        help="Number of recent events to display.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the parsed state as JSON instead of a TUI view.",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI colors.",
    )
    return parser.parse_args()


def format_dt(value: str | None) -> str:
    if not value:
        return "-"
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return value
    return dt.astimezone().strftime("%Y-%m-%d %H:%M:%S")


def format_duration(start_iso: str | None) -> str:
    if not start_iso:
        return "-"
    try:
        start = datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
    except ValueError:
        return "-"
    elapsed = datetime.now(timezone.utc) - start.astimezone(timezone.utc)
    total_seconds = max(0, int(elapsed.total_seconds()))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}h {minutes}m {seconds}s"
    if minutes:
        return f"{minutes}m {seconds}s"
    return f"{seconds}s"


def render_bar(percent: float | None, width: int = 20) -> str:
    if percent is None:
        return "-" * width
    bounded = max(0.0, min(100.0, percent))
    filled = round((bounded / 100.0) * width)
    return "#" * filled + "-" * (width - filled)


def trim_text(value: str | None, limit: int = 120) -> str:
    if not value:
        return "-"
    compact = " ".join(value.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


def format_percent(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.1f}%"


def shorten_path(value: str | None, levels: int) -> str:
    if not value:
        return "-"
    parts = Path(value).parts
    if levels <= 0 or len(parts) <= levels:
        return value
    return str(Path(*parts[-levels:]))


def supports_color(no_color: bool) -> bool:
    if no_color:
        return False
    if os.getenv("NO_COLOR"):
        return False
    return sys.stdout.isatty()


def colorize(text: str, color: str, enabled: bool) -> str:
    if not enabled:
        return text
    code = COLORS.get(color)
    if not code:
        return text
    return f"{code}{text}{RESET}"


def level_color(percent: float | None) -> str:
    if percent is None:
        return "bright_black"
    if percent >= 85:
        return "bright_red"
    if percent >= 60:
        return "bright_yellow"
    return "bright_green"


def status_symbol(is_running: bool) -> str:
    return ">" if is_running else "="


def phase_token(phase: str | None) -> str:
    if phase == "final_answer":
        return "final"
    if phase == "commentary":
        return "work"
    return phase or "-"


def render_meter(percent: float | None, width: int, enabled: bool) -> str:
    return colorize(render_bar(percent, width), level_color(percent), enabled)


def latest_session_file(root: Path) -> Path:
    files = [path for path in root.rglob("*.jsonl") if path.is_file()]
    if not files:
        raise FileNotFoundError(f"No session JSONL files found under {root}")
    return max(files, key=lambda path: path.stat().st_mtime)


@dataclass
class HudState:
    session_file: str = "-"
    session_id: str | None = None
    cwd: str | None = None
    start_time: str | None = None
    cli_version: str | None = None
    source: str | None = None
    model_context_window: int | None = None
    active_turn_id: str | None = None
    is_task_running: bool = False
    total_tokens: int | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    reasoning_output_tokens: int | None = None
    rate_primary_percent: float | None = None
    rate_secondary_percent: float | None = None
    rate_primary_reset: int | None = None
    rate_secondary_reset: int | None = None
    plan_type: str | None = None
    last_event_at: str | None = None
    last_agent_phase: str | None = None
    last_agent_message: str | None = None
    event_counts: dict[str, int] = field(default_factory=dict)
    recent_events: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_file": self.session_file,
            "session_id": self.session_id,
            "cwd": self.cwd,
            "start_time": self.start_time,
            "cli_version": self.cli_version,
            "source": self.source,
            "model_context_window": self.model_context_window,
            "active_turn_id": self.active_turn_id,
            "is_task_running": self.is_task_running,
            "total_tokens": self.total_tokens,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "reasoning_output_tokens": self.reasoning_output_tokens,
            "rate_primary_percent": self.rate_primary_percent,
            "rate_secondary_percent": self.rate_secondary_percent,
            "rate_primary_reset": self.rate_primary_reset,
            "rate_secondary_reset": self.rate_secondary_reset,
            "plan_type": self.plan_type,
            "last_event_at": self.last_event_at,
            "last_agent_phase": self.last_agent_phase,
            "last_agent_message": self.last_agent_message,
            "event_counts": self.event_counts,
            "recent_events": self.recent_events,
        }


class SessionMonitor:
    def __init__(self, session_file: Path, tail_events: int) -> None:
        self.session_file = session_file
        self.tail_events = tail_events
        self.offset = 0
        self.state = HudState(session_file=str(session_file))

    def reset(self, session_file: Path) -> None:
        self.session_file = session_file
        self.offset = 0
        self.state = HudState(session_file=str(session_file))

    def update(self) -> HudState:
        try:
            file_size = self.session_file.stat().st_size
        except FileNotFoundError:
            return self.state

        if file_size < self.offset:
            self.offset = 0
            self.state = HudState(session_file=str(self.session_file))

        with self.session_file.open("r", encoding="utf-8", errors="replace") as handle:
            handle.seek(self.offset)
            for raw_line in handle:
                line = raw_line.strip()
                if not line:
                    continue
                self.consume_line(line)
            self.offset = handle.tell()
        return self.state

    def consume_line(self, line: str) -> None:
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            return

        event_type = record.get("type")
        payload = record.get("payload") or {}
        timestamp = record.get("timestamp")
        self.state.last_event_at = timestamp
        self.state.event_counts[event_type] = self.state.event_counts.get(event_type, 0) + 1
        self._push_recent_event(event_type, payload, timestamp)

        if event_type == "session_meta":
            self.state.session_id = payload.get("id")
            self.state.cwd = payload.get("cwd")
            self.state.start_time = payload.get("timestamp") or timestamp
            self.state.cli_version = payload.get("cli_version")
            self.state.source = payload.get("source")
            return

        if event_type != "event_msg":
            return

        inner_type = payload.get("type")
        if inner_type == "task_started":
            self.state.active_turn_id = payload.get("turn_id")
            self.state.model_context_window = payload.get("model_context_window")
            self.state.is_task_running = True
        elif inner_type == "task_complete":
            self.state.active_turn_id = payload.get("turn_id") or self.state.active_turn_id
            self.state.is_task_running = False
            self.state.last_agent_phase = "final_answer"
            self.state.last_agent_message = payload.get("last_agent_message")
        elif inner_type == "agent_message":
            self.state.last_agent_phase = payload.get("phase")
            self.state.last_agent_message = payload.get("message")
        elif inner_type == "token_count":
            info = payload.get("info") or {}
            total_usage = info.get("total_token_usage") or {}
            self.state.input_tokens = total_usage.get("input_tokens", self.state.input_tokens)
            self.state.output_tokens = total_usage.get("output_tokens", self.state.output_tokens)
            self.state.reasoning_output_tokens = total_usage.get(
                "reasoning_output_tokens", self.state.reasoning_output_tokens
            )
            self.state.total_tokens = total_usage.get("total_tokens", self.state.total_tokens)

            model_context_window = info.get("model_context_window")
            if model_context_window:
                self.state.model_context_window = model_context_window
            rate_limits = payload.get("rate_limits") or {}
            primary = rate_limits.get("primary") or {}
            secondary = rate_limits.get("secondary") or {}
            self.state.rate_primary_percent = primary.get("used_percent", self.state.rate_primary_percent)
            self.state.rate_secondary_percent = secondary.get(
                "used_percent", self.state.rate_secondary_percent
            )
            self.state.rate_primary_reset = primary.get("resets_at", self.state.rate_primary_reset)
            self.state.rate_secondary_reset = secondary.get("resets_at", self.state.rate_secondary_reset)
            self.state.plan_type = rate_limits.get("plan_type", self.state.plan_type)

    def _push_recent_event(self, event_type: str, payload: dict[str, Any], timestamp: str | None) -> None:
        label = event_type
        if event_type == "event_msg":
            inner_type = payload.get("type", "unknown")
            label = f"event_msg:{inner_type}"
        elif event_type == "response_item":
            label = f"response_item:{payload.get('type', 'unknown')}"
        entry = f"{format_dt(timestamp)} | {label}"
        self.state.recent_events.append(entry)
        if len(self.state.recent_events) > self.tail_events:
            self.state.recent_events = self.state.recent_events[-self.tail_events :]


def reset_epoch_to_text(epoch_seconds: int | None) -> str:
    if not epoch_seconds:
        return "-"
    try:
        dt = datetime.fromtimestamp(epoch_seconds, tz=timezone.utc).astimezone()
    except (OverflowError, OSError, ValueError):
        return "-"
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def render_single(state: HudState, path_levels: int, color_enabled: bool) -> str:
    symbol = colorize(status_symbol(state.is_task_running), "cyan", color_enabled)
    cwd = colorize(shorten_path(state.cwd, path_levels), "bright_blue", color_enabled)
    phase = colorize(phase_token(state.last_agent_phase), "magenta", color_enabled)
    primary = colorize(format_percent(state.rate_primary_percent), level_color(state.rate_primary_percent), color_enabled)
    secondary = colorize(
        format_percent(state.rate_secondary_percent),
        level_color(state.rate_secondary_percent),
        color_enabled,
    )
    message = trim_text(state.last_agent_message, 36)
    return (
        f"[{symbol}] {cwd} | {phase} | {format_duration(state.start_time)}"
        f" | u:{primary} | w:{secondary} | {message}"
    )


def render_compact(state: HudState, path_levels: int, color_enabled: bool) -> str:
    status = colorize(
        "RUN" if state.is_task_running else "IDLE",
        "cyan" if state.is_task_running else "bright_black",
        color_enabled,
    )
    symbol = colorize(status_symbol(state.is_task_running), "cyan", color_enabled)
    cwd = colorize(shorten_path(state.cwd, path_levels), "bright_blue", color_enabled)
    phase = colorize(phase_token(state.last_agent_phase), "magenta", color_enabled)
    primary_bar = render_meter(state.rate_primary_percent, width=10, enabled=color_enabled)
    secondary_bar = render_meter(state.rate_secondary_percent, width=10, enabled=color_enabled)
    primary_value = colorize(
        format_percent(state.rate_primary_percent),
        level_color(state.rate_primary_percent),
        color_enabled,
    )
    secondary_value = colorize(
        format_percent(state.rate_secondary_percent),
        level_color(state.rate_secondary_percent),
        color_enabled,
    )
    line1 = (
        f"[{symbol} {status}] {cwd} | {phase} | {format_duration(state.start_time)}"
        f" | plan:{state.plan_type or '-'}"
    )
    line2 = (
        f"ctx:{state.model_context_window or '-'}"
        f" | usage:{primary_bar} {primary_value}"
        f" | week:{secondary_bar} {secondary_value}"
        f" | msg:{trim_text(state.last_agent_message, 52)}"
    )
    return "\n".join((line1, line2))


def render_expanded(state: HudState, color_enabled: bool) -> str:
    lines: list[str] = []
    lines.append(colorize("Codex HUD Prototype", "cyan", color_enabled))
    lines.append(colorize("=" * 80, "bright_black", color_enabled))
    lines.append(f"Session file : {state.session_file}")
    lines.append(f"Session id   : {state.session_id or '-'}")
    lines.append(
        f"Status       : "
        f"{colorize('RUNNING' if state.is_task_running else 'IDLE', 'cyan' if state.is_task_running else 'bright_black', color_enabled)}"
    )
    lines.append(f"Started      : {format_dt(state.start_time)}")
    lines.append(f"Elapsed      : {format_duration(state.start_time)}")
    lines.append(f"CWD          : {state.cwd or '-'}")
    lines.append(f"CLI / source : {state.cli_version or '-'} / {state.source or '-'}")
    lines.append(f"Plan         : {state.plan_type or '-'}")
    lines.append("")
    lines.append(
        f"Context      : window={state.model_context_window or '-'} "
        f"(current occupancy not exposed by local session JSONL)"
    )
    lines.append(
        f"Session toks : total={state.total_tokens or '-'} input={state.input_tokens or '-'} "
        f"output={state.output_tokens or '-'} reasoning={state.reasoning_output_tokens or '-'} "
        f"(cumulative)"
    )
    lines.append(
        f"Primary      : [{render_meter(state.rate_primary_percent, 20, color_enabled)}] "
        f"{colorize(format_percent(state.rate_primary_percent), level_color(state.rate_primary_percent), color_enabled)} "
        f"reset={reset_epoch_to_text(state.rate_primary_reset)}"
    )
    lines.append(
        f"Secondary    : [{render_meter(state.rate_secondary_percent, 20, color_enabled)}] "
        f"{colorize(format_percent(state.rate_secondary_percent), level_color(state.rate_secondary_percent), color_enabled)} "
        f"reset={reset_epoch_to_text(state.rate_secondary_reset)}"
    )
    lines.append("")
    lines.append(f"Last phase   : {state.last_agent_phase or '-'}")
    lines.append(f"Last event   : {format_dt(state.last_event_at)}")
    lines.append(f"Last message : {trim_text(state.last_agent_message, 160)}")
    lines.append("")
    lines.append(colorize("Event counts", "cyan", color_enabled))
    lines.append(colorize("-" * 80, "bright_black", color_enabled))
    if state.event_counts:
        for key in sorted(state.event_counts):
            lines.append(f"{key:<18} {state.event_counts[key]}")
    else:
        lines.append("-")
    lines.append("")
    lines.append(colorize("Recent events", "cyan", color_enabled))
    lines.append(colorize("-" * 80, "bright_black", color_enabled))
    if state.recent_events:
        lines.extend(state.recent_events)
    else:
        lines.append("-")
    return "\n".join(lines)


def render_text(state: HudState, layout: str, path_levels: int, color_enabled: bool) -> str:
    if layout == "single":
        return render_single(state, path_levels, color_enabled)
    if layout == "compact":
        return render_compact(state, path_levels, color_enabled)
    return render_expanded(state, color_enabled)


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def main() -> int:
    args = parse_args()
    color_enabled = supports_color(args.no_color)
    session_file = args.session or latest_session_file(args.sessions_root)
    monitor = SessionMonitor(session_file=session_file, tail_events=args.tail_events)

    def refresh_session_choice() -> None:
        if args.session:
            return
        latest = latest_session_file(args.sessions_root)
        if latest != monitor.session_file:
            monitor.reset(latest)

    while True:
        refresh_session_choice()
        state = monitor.update()
        if args.json:
            print(json.dumps(state.to_dict(), ensure_ascii=False, indent=2))
            return 0

        if args.watch:
            clear_screen()
        print(render_text(state, args.layout, args.path_levels, color_enabled))

        if not args.watch:
            return 0
        try:
            time.sleep(max(0.2, args.interval))
        except KeyboardInterrupt:
            return 0


if __name__ == "__main__":
    sys.exit(main())
