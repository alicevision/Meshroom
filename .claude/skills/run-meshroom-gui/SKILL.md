---
name: run-meshroom-gui
description: Launch and drive the Meshroom GUI (PySide6/QML) to check a UI change works, without leaving a frozen window behind. Use whenever you need to start the GUI, load a project in it, or script interactions with it.
---

# Running the Meshroom GUI for testing

Never launch `start.sh` / `python meshroom/ui` directly from an agent shell, and never write an ad-hoc
driver that calls `MeshroomApp(...).exec()`. If the run is interrupted or times out, the wrapper process
dies, but the GUI swallows SIGINT inside Qt callbacks and keeps running as an orphan — on the user's
display if not offscreen — frozen, until someone kills it.

Use the launcher in this directory instead. It runs offscreen, restores the default SIGINT handling
(as `meshroom/ui/__main__.py` does), sets a watchdog and a hard timeout, runs in its own process group
and kills that group at the end.

## Smoke test

```bash
.claude/skills/run-meshroom-gui/runGui.sh -t 120 -l "$SCRATCH/gui.log" /path/to/project.mg
```

Arguments after the options are passed to Meshroom (project file, `-p pipeline`, ...).
Exit status 0 means the UI loaded and quit cleanly; read the log for QML/Python warnings.

## Driving the UI with a scenario

Write a scenario file (in your scratch directory, not in the repo) defining `run(app, done)`:

```python
from PySide6.QtCore import QTimer

def run(app, done):
    scene = app._activeProject           # meshroom.ui.reconstruction / scene object (`_currentScene` in QML)
    node = scene.graph.node("CameraInit_1")
    scene.setActiveNode(node)
    print("=== DRIVE: active", node.name, flush=True)
    QTimer.singleShot(3000, done)        # let the UI react, then quit; done(1) to report a failure
```

```bash
.claude/skills/run-meshroom-gui/runGui.sh -t 180 -l "$SCRATCH/gui.log" \
    --scenario "$SCRATCH/scenario.py" --delay 8 /path/to/project.mg
grep "=== DRIVE" "$SCRATCH/gui.log"
```

Driver options: `--scenario FILE`, `--delay` (seconds before `run` is called, default 8),
`--watchdog` (seconds before stacks are dumped and the process exits, default 180).
Keep `-t` (launcher timeout) above `--watchdog` so the stack dump gets a chance to print.

To reach QML items, use `findChildren` on `app.engine.rootObjects()` (and on `contentItem()` of windows)
and match `metaObject().className()` (e.g. `GraphEditor_QMLTYPE_*`); do not walk properties by hand.

## Options and environment

- `-v`: show the window on `$DISPLAY`. Only when the user asks to see it.
- `-t SECONDS`: hard timeout of the whole run (default 240).
- `-l FILE`: log file (default stdout).
- `MESHROOM_ENV_CMD`: prefix providing the Python environment (PySide6, AliceVision plugin...),
  e.g. `MESHROOM_ENV_CMD="rez env meshroom --"`. Default: none.
- `MESHROOM_PYTHON`: interpreter (default `python3`).

## After the run

The launcher reports `processes still alive in group N` if anything survived. If you ever launched the
GUI another way, check `ps -eo pid,args | grep driveMeshroom` and kill what you started before finishing.
