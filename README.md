# PyRamUtil

PyRamUtil is a Windows memory monitoring and analysis tool focused on behavior, not just usage.

Unlike Task Manager, PyRamUtil tracks RAM usage over time, analyzes per-process memory patterns, and explains what is happening — such as startup allocations, temporary spikes, or steady growth that may indicate leaks.

The project is designed as a lightweight monitoring engine with both CLI and GUI frontends.

---

## Features

- Time-based RAM monitoring (not just snapshots)
- Per-process memory tracking
- Detection of memory behavior patterns:
  - Startup allocations
  - Temporary memory bursts
  - Steady memory growth
- System-level memory pressure explanation
- CLI-first design with optional GUI
- No kernel drivers or admin privileges required

---

## Screenshots

(Coming soon)

---

## Requirements

- Windows 10 or later
- Python 3.9+

---

## Installation

Clone the repository and install dependencies:

```bash
pip install -r requirements.txt
