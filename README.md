# PyRamUtil (Check out the release for final executable file!)

PyRamUtil is a Windows memory monitoring and analysis tool focused on behavior, not just usage.

Unlike Task Manager, PyRamUtil tracks RAM usage over time, analyzes per-process memory patterns, and explains what is happening — such as startup allocations, temporary spikes, or steady growth that may indicate leaks.

The project is designed as a lightweight monitoring engine with both CLI and GUI frontends.

  -- *Heavy AI Useage warning, something I am not proud of* --

-- This project is just a prototype, you can add your own features as required, it is finished for the most part, I will revisit it if there are some bugs. --

---

## Features

- Live RAM monitoring with historical context (not just snapshots)
- Real-time per-process memory tracking (apps and system services)
- Clear attribution using private memory (no double-counting)
- System memory condition detection (healthy / pressured / critical)
- Live RAM usage graph (used vs total)
- Process view with sortable RAM usage (RSS and private memory)
- Dark-mode GUI with an engine-first architecture
- No kernel drivers, background services, or admin privileges required

---

## Bug

- Double click RSS in processes tab 2-3 times for everything to appear.

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







