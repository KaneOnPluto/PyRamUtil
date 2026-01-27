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
```
---

## Execution

```bash
python main.py
```
- This mode is pure CLI
  
- The CLI output shows:

   1) Process start/exit events

   2) Significant memory changes

   3) Behavior classifications and warnings

   4) System memory pressure explanations

- GUI mode -

```bash
python gui.py
```
- The GUI mode provides a live view of system memory and process-level changes using the same underlying engine.

---

PolyForm Noncommercial License 1.0.0

This project is source-available.
You may use, modify, and redistribute it for personal and non-commercial purposes only.
Commercial use is not permitted.







