import time
import psutil
from collections import deque


process_history = {}
growth_tracker = {}
system_history = deque(maxlen=60)
role_history = deque(maxlen=60)

MB = 1024 * 1024
MEMORY_DELTA_THRESHOLD = 5 * MB
HISTORY_LENGTH = 6
STEADY_GROWTH_THRESHOLD = 4
SPIKE_MB = 30 * MB
FLAT_DELTA_MB = 5 * MB


def fmt_mb(value):
    if value is None:
        return "N/A"
    return f"{value / MB:.2f} MB"


def get_rss_deltas(samples):
    return [samples[i][1] - samples[i - 1][1] for i in range(1, len(samples))]


def get_system_memory():
    vm = psutil.virtual_memory()
    sm = psutil.swap_memory()

    return {
        "total": vm.total,
        "available": vm.available,
        "used": vm.used,
        "cached": getattr(vm, "cached", None),
        "commit_used": sm.used,
        "commit_total": sm.total,
    }


def classify_process(name):
    name = name.lower()

    if name in ("system idle process", "system"):
        return "system_service"
    if name in ("svchost.exe", "services.exe", "wininit.exe"):
        return "system_service"
    if name in ("explorer.exe", "taskhostw.exe"):
        return "system_ui"
    return "user_app"


def get_process_snapshot():
    processes = []

    for proc in psutil.process_iter(["pid", "name"]):
        try:
            name = proc.info.get("name") or "unknown"
            mem = proc.memory_info()
            rss = mem.rss

            try:
                full = proc.memory_full_info()
                private = full.private
            except (psutil.AccessDenied, AttributeError):
                private = 0

            processes.append(
                {
                    "pid": proc.pid,
                    "name": name,
                    "rss": rss,
                    "private": private,
                    "role": classify_process(name),
                }
            )

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return processes


def take_snapshot():
    return {
        "timestamp": time.time(),
        "system": get_system_memory(),
        "processes": {p["pid"]: p for p in get_process_snapshot()},
    }


def diff_snapshots(prev, curr):
    changes = {
        "new_processes": [],
        "terminated_processes": [],
        "memory_changes": [],
    }

    prev_pids = set(prev["processes"])
    curr_pids = set(curr["processes"])

    for pid in curr_pids - prev_pids:
        changes["new_processes"].append(curr["processes"][pid])

    for pid in prev_pids - curr_pids:
        changes["terminated_processes"].append(prev["processes"][pid])

    for pid in prev_pids & curr_pids:
        prev_p = prev["processes"][pid]
        curr_p = curr["processes"][pid]

        delta = curr_p["rss"] - prev_p["rss"]
        if abs(delta) >= MEMORY_DELTA_THRESHOLD:
            changes["memory_changes"].append(
                {
                    "pid": pid,
                    "name": curr_p["name"],
                    "delta": delta,
                    "rss": curr_p["rss"],
                }
            )

    return changes


def update_process_history(snapshot):
    timestamp = snapshot["timestamp"]

    for pid, proc in snapshot["processes"].items():
        if pid not in process_history:
            process_history[pid] = {
                "name": proc["name"],
                "rss": deque(maxlen=HISTORY_LENGTH),
            }

        process_history[pid]["rss"].append((timestamp, proc["rss"]))

    alive = set(snapshot["processes"])
    for pid in list(process_history):
        if pid not in alive:
            del process_history[pid]


def detect_startup_spike(pid):
    samples = process_history[pid]["rss"]
    if len(samples) < 3:
        return False

    deltas = get_rss_deltas(samples)
    return deltas[0] > SPIKE_MB and all(abs(d) < FLAT_DELTA_MB for d in deltas[1:])


def detect_temporary_burst(pid):
    samples = process_history[pid]["rss"]
    if len(samples) < 3:
        return False

    values = [rss for _, rss in samples]
    return max(values) - values[-1] > FLAT_DELTA_MB


def detect_steady_growth(pid):
    samples = process_history[pid]["rss"]
    if len(samples) < STEADY_GROWTH_THRESHOLD + 1:
        return False

    increases = sum(
        samples[i][1] > samples[i - 1][1] for i in range(1, len(samples))
    )
    return increases >= STEADY_GROWTH_THRESHOLD


def explain_system_pressure(system):
    used_ratio = system["used"] / system["total"]
    available_ratio = system["available"] / system["total"]

    if used_ratio > 0.85 and available_ratio > 0.20:
        return "High RAM usage but sufficient available memory"
    if available_ratio < 0.10:
        return "Low available memory — system under pressure"
    return "Memory usage within normal range"


def system_condition(system):
    used_ratio = system["used"] / system["total"]
    available_ratio = system["available"] / system["total"]

    if available_ratio < 0.08:
        return "critical"
    if used_ratio > 0.85:
        return "pressured"
    return "healthy"


def engine_tick(prev_snapshot):
    curr = take_snapshot()
    update_process_history(curr)
    diff = diff_snapshots(prev_snapshot, curr)

    role_breakdown = aggregate_memory_by_role(curr["processes"])
    condition = system_condition(curr["system"])
    condition_text = explain_system_pressure(curr["system"])

    system_history.append(curr["system"])
    role_history.append(role_breakdown)

    return curr, {
        "timestamp": curr["timestamp"],
        "system": curr["system"],
        "condition": condition,
        "condition_text": condition_text,
        "roles": role_breakdown,
        "diff": diff,
        "processes": curr["processes"],
    }


def aggregate_memory_by_role(processes):
    totals = {
        "user_app": 0,
        "system_service": 0,
        "system_ui": 0,
        "other": 0,
    }

    for p in processes.values():
        role = p.get("role", "other")
        private = p.get("private", 0)
        totals[role] += private

    return totals


def main():
    prev = take_snapshot()
    update_process_history(prev)
    time.sleep(5)

    while True:
        curr = take_snapshot()
        update_process_history(curr)
        diff = diff_snapshots(prev, curr)
        print(explain_system_pressure(curr["system"]))
        prev = curr
        time.sleep(5)


if __name__ == "__main__":
    main()
