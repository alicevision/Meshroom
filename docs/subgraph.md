# Subgraphs

A **subgraph** is a chain of **live nodes** run as **one task**, in one software session (its *context*), in memory, without cache files between the nodes. It looks like a standard Meshroom node (`SubGraph`): on a farm it takes one machine (or one machine per group of frames), whatever the number of nodes it contains.

Typical uses:
- compositing: a graph of image operations is one task per frame range, not one task per operation;
- Houdini / Maya / Nuke: open the software once, open a scene, change parameters, export or render, then close it;
- from a software: run a Meshroom template in the Python shell of Houdini, Maya or Nuke, in the open session, as fast as running the scripts of its nodes one after the other.

## Nodes

| Node | Role |
|------|------|
| `SubGraph` | Runs a subgraph as a task (local or farm). Its inputs `ins` are the ports of the `GraphInput` node of the subgraph, its outputs `outs` those of its `GraphOutput` node. |
| `GraphInput` | Entry of the subgraph: one output per port (`Ports`: `image, mask, count:IntParam`), plus `iteration` and `frame`. At most one per subgraph, optional. |
| `GraphOutput` | Exit of the subgraph: one input per port. At most one per subgraph, optional. |
| `LiveSubGraph` | A subgraph inside a subgraph, run in the same session, with its own loop. |
| `LiveScript` | Python code run in the context: reads `ins`, `ctx`, `session`; fills `outs`. |
| `HoudiniOpenScene`, `HoudiniSetParms`, `HoudiniRender`, `HoudiniSaveScene` | Houdini operations (context `houdini`). |

A subgraph only contains live nodes (`desc.LiveNode`, see [NODE_DEVELOPMENT.md](../NODE_DEVELOPMENT.md)); any value goes through their connections (an image buffer, a `hou.Node`, a list...). Nodes without connections between them can be ordered with flow connections.

### Where the subgraph is stored

- **Embedded** in the node (`Embedded Subgraph`, JSON): double-click the node to edit it.
- **Template** (`Template`: a `.mgt`, saved with *File > Save As Template*): used when there is no embedded subgraph. Editing it (double-click) writes the template file. *Make Local* copies the template into the node.

### Context

`Context` is the software in which the nodes run: `auto` (the one the nodes need, Python if none), `python`, `houdini`, `maya`, `nuke`. It is opened once for the whole run (all iterations, nested subgraphs) and closed at the end.

When the context is not available in the Python of Meshroom (no `hou` module...), the task runs in the interpreter of the context:

| Context | Interpreter | Override |
|---------|-------------|----------|
| houdini | `hython` | `MESHROOM_HYTHON` |
| maya | `mayapy` | `MESHROOM_MAYAPY` |
| nuke | `nuke -t` | `MESHROOM_NUKE` |

That interpreter must be able to import Meshroom and its dependencies (e.g. `psutil`): the `PYTHONPATH` of Meshroom is passed to it; with another Python version, add a matching `site-packages` folder.

### Loops

| Loop | Behaviour |
|------|-----------|
| none | runs once |
| count | `Iterations` runs; the outputs of an iteration feed the inputs of the same name of the next one (a feedback, e.g. a fractal) |
| frames | runs once per frame from `First Frame` to `Last Frame` every `Frame Step`; `Frames Per Task` splits the range in tasks (farm), 0 for one task |

The live nodes read `ctx.iteration` and `ctx.frame` (also outputs of `GraphInput`); the current frame of Houdini / Maya / Nuke follows the frame loop. A `LiveSubGraph` without its own loop sees the frame of its parent.

## User interface

- **Double-click** a `SubGraph` / `LiveSubGraph` node (or select it and press **Ctrl+Enter**) to show its subgraph.
- The **breadcrumb** at the top of the Graph Editor shows the path from the project; click an element (or **Ctrl+Backspace**) to go back. Leaving writes the subgraph back in its node; the ports of the node follow its `GraphInput` / `GraphOutput`.
- **Run Live** (play button of the bar) runs the subgraph now with the inputs of its node: in Meshroom for Python, else in the interpreter of its context. A frame loop runs its first frame only. The duration and the outputs are shown in the bar.
- Saving, computing or submitting from a subgraph acts on the project (the subgraphs are written back first). The undo history is cleared when entering or leaving a subgraph.

## From a software

```python
# Houdini Python shell (Meshroom in PYTHONPATH, MESHROOM_NODES_PATH / MESHROOM_PLUGINS_PATH for other nodes)
import meshroom.subgraph

outputs = meshroom.subgraph.run("/path/houdiniRender.mgt", {"hipFile": hou.hipFile.path(), "scale": 2.0})
outputs = meshroom.subgraph.run("/path/houdiniRender.mgt", {"scale": 2.0}, frames=(1001, 1010))
outputs = meshroom.subgraph.run("/path/feedback.mgt", {"value": 1}, iterations=5)
```

The session of the software is used as it is: `HoudiniOpenScene` does not reload the scene if it is already the current one, and nothing is closed at the end. To run a template many times, load it once with `plan = meshroom.subgraph.load(path)` and pass `plan` to `run`.

## Examples

- [subgraph/pythonFeedback.mgt](subgraph/pythonFeedback.mgt): a `LiveScript` in a count loop (no software needed).
- [subgraph/houdiniRender.mgt](subgraph/houdiniRender.mgt): open a scene, set parameters, render the frame of the loop.

## Writing a context

```python
from meshroom.core.subgraph import LiveContext, registerContext

class BlenderContext(LiveContext):
    interpreterVariable = "MESHROOM_BLENDER"
    defaultInterpreter = "python3.11"  # a Python with the bpy module

    @classmethod
    def isAvailable(cls):
        try:
            import bpy
            return True
        except ImportError:
            return False

    def open(self):
        import bpy
        super().open()
        self.session = bpy

    def beginStep(self, iteration, frame):
        if frame is not None:
            self.session.context.scene.frame_set(frame)

registerContext("blender", BlenderContext)
```

`ownsSession` is True when the run is a task of Meshroom or of a farm (the session can be cleaned in `close`), False from a script or the shell of the software.
