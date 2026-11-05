#!/usr/bin/env python3
"""Read-only ADB playback observations. Never equates counters with visible motion."""
import argparse
import json
import re
import subprocess
import time
from pathlib import Path

PACKAGE = "com.metrixneo.tv"
LAYER = re.compile(r"SurfaceView\[com\.metrixneo\.tv/com\.metrixneo\.tv\.MainActivity\]\(BLAST\)#\d+")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adb", required=True)
    parser.add_argument("--serial", required=True)
    parser.add_argument("--seconds", type=int, default=90)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not 10 <= args.seconds <= 3600:
        parser.error("--seconds must be between 10 and 3600")

    def shell(command, allow_nonzero=False):
        result = subprocess.run([args.adb, "-s", args.serial, "shell", command],
                                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=15)
        if result.returncode and not allow_nonzero:
            raise RuntimeError("ADB read failed")
        return result.stdout

    def pid():
        value = shell("pidof " + PACKAGE, allow_nonzero=True).strip()
        return value if value.isdigit() else None

    initial_pid = pid()
    if not initial_pid:
        raise SystemExit("Neo is not running; open the channel before measuring.")
    layers = shell("dumpsys SurfaceFlinger --list").splitlines()
    layer = next((line for line in layers if LAYER.fullmatch(line)), None)

    def logs(process):
        return shell("logcat -d --pid=" + process + " -s NeoPlayback:I NeoZap:I NeoBuffer:I '*:S'").splitlines()

    seen = set(logs(initial_pid))
    samples, changes, errors, present = [], [], [], set()
    start = time.monotonic()
    next_logs = 0.0
    process_gone = False
    presentation_floor = None
    previous_latest = None
    last_presentation_advance = time.monotonic()
    longest_no_advance_ms = 0.0
    while time.monotonic() - start < args.seconds:
        elapsed = time.monotonic() - start
        try:
            if elapsed >= next_logs:
                current_pid = pid()
                if current_pid != initial_pid:
                    process_gone = True
                    errors.append({"at_seconds": round(elapsed, 2), "type": "process_changed_or_exited"})
                    break
                for line in logs(initial_pid):
                    if line in seen:
                        continue
                    seen.add(line)
                    match = re.search(r"(NeoPlayback|NeoZap|NeoBuffer)\s*:\s*(.*)", line)
                    if not match:
                        continue
                    fields = dict(re.findall(r"(\w+)=([\w.-]+)", match[2]))
                    # Only structured numerical/state fields; no channel references or URLs.
                    keep = {key: value for key, value in fields.items() if key in {
                        "id", "state", "playing", "position_ms", "buffered_ms", "rendered", "dropped",
                        "value", "elapsed_ms", "profile", "start_ms", "rebuffer_ms", "max_ms", "code"}}
                    entry = {"observed_seconds": round(elapsed, 2), "tag": match[1], **keep}
                    if match[1] == "NeoPlayback":
                        samples.append(entry)
                    else:
                        changes.append(entry)
                next_logs = elapsed + 5
            if layer:
                output = shell("dumpsys SurfaceFlinger --latency '" + layer + "'")
                current_times = []
                for line in output.splitlines()[1:]:
                    values = line.split()
                    if len(values) == 3 and all(value.isdigit() for value in values):
                        timestamp = int(values[1])
                        if 0 < timestamp < 9223372036854775807:
                            current_times.append(timestamp)
                if current_times:
                    latest = max(current_times)
                    if presentation_floor is None:
                        presentation_floor = latest
                    present.update(value for value in current_times if value >= presentation_floor)
                    now = time.monotonic()
                    if latest != previous_latest:
                        previous_latest = latest
                        last_presentation_advance = now
                    else:
                        longest_no_advance_ms = max(longest_no_advance_ms, (now-last_presentation_advance)*1000)
        except (RuntimeError, subprocess.TimeoutExpired):
            errors.append({"at_seconds": round(elapsed, 2), "type": "adb_read_unavailable"})
            if len(errors) >= 3:
                break
        time.sleep(1)

    times = sorted(present)
    gaps = [(after - before) / 1e6 for before, after in zip(times, times[1:])]
    clock_stalls, counter_stalls = [], []
    for before, after in zip(samples, samples[1:]):
        if before.get("id") != after.get("id") or after.get("playing") != "true":
            continue
        duration = after["observed_seconds"] - before["observed_seconds"]
        if duration < 2:
            continue
        if before.get("position_ms") == after.get("position_ms"):
            clock_stalls.append(round(duration, 2))
        if before.get("rendered") == after.get("rendered"):
            counter_stalls.append(round(duration, 2))
    summary = {
        "duration_seconds": round(time.monotonic() - start, 2),
        "app_process_survived": not process_gone,
        "player_samples": len(samples),
        "distinct_presentation_timestamps": len(present),
        "max_presentation_gap_ms": round(max(gaps), 3) if gaps else None,
        "max_no_presentation_advance_ms": round(longest_no_advance_ms, 2),
        "presentation_gaps_over_500ms": [round(gap, 2) for gap in gaps if gap > 500],
        "player_clock_stalls_seconds": clock_stalls,
        "video_output_counter_stalls_seconds": counter_stalls,
        "read_errors": len(errors),
        "visible_motion_verified": False,
        "limitation": "Android presentation/counter measurements do not observe the final panel pixels. No freeze-free verdict is possible from this report alone.",
    }
    report = {"summary": summary, "player_samples": samples, "state_changes": changes, "errors": errors}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    if len(samples) < 2 or len(present) < 2:
        return 3  # Insufficient observation, never a successful fluidity verdict.
    return 2 if process_gone or errors or longest_no_advance_ms > 500 or summary["presentation_gaps_over_500ms"] or clock_stalls or counter_stalls else 0


if __name__ == "__main__":
    raise SystemExit(main())
