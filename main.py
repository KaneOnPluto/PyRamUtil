import time
import psutil
from collections import deque


# ------------------------
# Global settings
# ------------------------
process_history = {}
growth_tracker = {}


# ------------------------
# Constants
# ------------------------
MB = 1024 * 1024
MEMORY_DELTA_THRESHOLD = 5 * MB 
HISTORY_LENGTH = 6  # number of samples to keep
STEADY_GROWTH_THRESHOLD = 4  # how many consecutive increases
SPIKE_MB = 30 * MB
FLAT_DELTA_MB = 5 * MB


# ------------------------
# Helpers
# ------------------------
def fmt_mb(value):
    if value is None:
        return "N/A"
    return f"{value / MB:.2f} MB"


def get_rss_deltas(samples):
    return [samples[i][1] - samples[i - 1][1] for i in range(1, len(samples))]


# ------------------------
# Data collection
# ------------------------
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


def get_process_snapshot():
    processes = []

    for proc in psutil.process_iter(["pid", "name", "memory_info", "create_time"]):
        try:
            mem = proc.info["memory_info"]
            processes.append(
                {
                    "pid": proc.info["pid"],
                    "name": proc.info["name"],
                    "rss": mem.rss,
                    "private": getattr(mem, "private", None),
                    "shared": getattr(mem, "shared", None),
                    "start_time": proc.info["create_time"],
                }
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return processes


def detect_startup_spike(pid):
    data = process_history[pid]
    samples = data["rss"]

    if len(samples) < 3:
        return False

    deltas = get_rss_deltas(samples)

    big_spike = deltas[0] > SPIKE_MB
    mostly_flat = all(abs(d) < FLAT_DELTA_MB for d in deltas[1:])

    return big_spike and mostly_flat


def detect_temporary_burst(pid):
    samples = process_history[pid]["rss"]

    if len(samples) < 3:
        return False

    values = [rss for _, rss in samples]
    return max(values) - values[-1] > FLAT_DELTA_MB


# ------------------------
# Snapshot + diff logic
# ------------------------
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

    # Memory deltas
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

    # Cleanup dead processes
    alive_pids = set(snapshot["processes"].keys())
    for pid in list(process_history.keys()):
        if pid not in alive_pids:
            del process_history[pid]


def detect_steady_growth(pid):
    samples = process_history[pid]["rss"]

    if len(samples) < STEADY_GROWTH_THRESHOLD + 1:
        return False

    increases = 0
    for i in range(1, len(samples)):
        if samples[i][1] > samples[i - 1][1]:
            increases += 1

    return increases >= STEADY_GROWTH_THRESHOLD


def explain_system_pressure(system):
    used_ratio = system["used"] / system["total"]
    available_ratio = system["available"] / system["total"]

    if used_ratio > 0.85 and available_ratio > 0.20:
        return "High RAM usage but sufficient available memory (likely cache)"
    elif available_ratio < 0.10:
        return "Low available memory — system under pressure"
    else:
        return "Memory usage within normal range"


def print_top_offenders():
    if not growth_tracker:
        return

    print("Top memory growth offenders:")
    sorted_growth = sorted(growth_tracker.items(), key=lambda x: x[1], reverse=True)

    for pid, delta in sorted_growth[:3]:
        name = process_history.get(pid, {}).get("name", "unknown")
        print(f"  {name:<15} +{delta / MB:.1f} MB")
        
def engine_tick(prev_snapshot):
    curr = take_snapshot()
    update_process_history(curr)
    diff = diff_snapshots(prev_snapshot, curr)

    state = {
        "timestamp": curr["timestamp"],
        "system": curr["system"],
        "diff": diff,
        "history": process_history.copy(),
    }

    return curr, state



# ------------------------
# output
# ------------------------
def print_system_memory(mem):
    for k, v in mem.items():
        print(f"{k:15}: {fmt_mb(v)}")


def print_diff(diff):
    for p in diff["new_processes"]:
        print(f"[+] Started  {p['name']} ({p['pid']})")

    for p in diff["terminated_processes"]:
        print(f"[-] Exited   {p['name']} ({p['pid']})")

    for m in diff["memory_changes"]:
        pid = m["pid"]
        growth_tracker[pid] = growth_tracker.get(pid, 0) + m["delta"]
        sign = "+" if m["delta"] > 0 else "-"
        print(
            f"[Δ] {m['name']:<20} "
            f"{sign}{abs(m['delta']) / MB:.1f} MB "
            f"(RSS {m['rss'] / MB:.1f} MB)"
        )


def print_behavior_classification():
    for pid, data in process_history.items():
        rss_mb = data["rss"][-1][1] / MB

        if detect_startup_spike(pid):
            print(f"[INFO] {data['name']} startup allocation (RSS {rss_mb:.1f} MB)")
        elif detect_temporary_burst(pid):
            print(f"[INFO] {data['name']} temporary memory burst (RSS {rss_mb:.1f} MB)")
        elif detect_steady_growth(pid):
            print(f"[WARN] {data['name']} steady memory growth (RSS {rss_mb:.1f} MB)")


# ------------------------
# Entry point
# ------------------------
def main():
    print("Initial system memory:")
    print_system_memory(get_system_memory())
    print("-" * 50)

    prev = take_snapshot()
    update_process_history(prev)
    time.sleep(5)

    while True:
        curr = take_snapshot()
        update_process_history(curr)
        diff = diff_snapshots(prev, curr)
        pressure = explain_system_pressure(curr["system"])
        print(f"[SYS] {pressure}")
        print_diff(diff)
        print_behavior_classification()
        print("-" * 50)
        prev = curr
        time.sleep(5)


if __name__ == "__main__":
    main()
