# Subgraphs

A **subgraph** is a chain of nodes run as **one task**, in one software session (its *context*), the values going from node to node in memory. It looks like a standard Meshroom node (`SubGraph`): on a farm it takes one machine (or one machine per group of frames), whatever the number of nodes it contains.

Typical uses:
- compositing: a graph of image operations is one task per frame range, not one task per operation;
- Houdini / Maya / Nuke: open the software once, open a scene, change parameters, export or render, then close it;
- from a software: run a Meshroom template in the Python shell of Houdini, Maya or Nuke, in the open session, as fast as running the scripts of its nodes one after the other.

## Nodes

| Node | Role |
|------|------|
| `SubGraph` | Runs a subgraph as a task (local or farm). Its inputs `ins` are the ports of the `GraphInput` node of the subgraph, its outputs `outs` those of its `GraphOutput` node. |
| `GraphInput` | Entry of the subgraph: one output per port, plus the loop state (`iteration` in a count loop; `frame`, the `frameRange` group (`start`, `stop`, as in HoudiniSetFrameRange) and `frameStep` in a frame range loop). At most one per subgraph. |
| `GraphOutput` | Exit of the subgraph: one input per port. At most one per subgraph, optional. |
| `LiveScript` | Python code run in the context: reads `ins`, `ctx`, `session`; fills `outs`. |
| `HoudiniScene`, `MayaScene`, `NukeScene` | The scene, the value that prevails: in a Meshroom task, opens `Scene File` (e.g. given by a pipeline node); in a session of the software, the open scene (`Scene File` is not read), unless `In ... Session` is `sceneFile`. |
| `HoudiniSave`, `MayaSave`, `NukeSave` | Saves the scene once. In a session of the software, only if `Save In ... Session` is on. |
| `HoudiniSetParms`, `HoudiniRender` | Houdini operations written as live nodes. |

### Any node in a subgraph

A subgraph can contain **any node**, and a node behaves according to where it is: at the top of a project it is a task (its own process, its own farm job); in a subgraph it runs in the process and the session of the subgraph, after the nodes it reads, and its outputs go to the next nodes in memory.
- **Task nodes** (`desc.Node`, e.g. the Houdini nodes of a pipeline plugin with `pythonExecutable = "hython"`): their `process` / `processChunk` is called as is. The context is deduced from their interpreter (hython: Houdini, mayapy: Maya, nuke: Nuke).
- **Command line nodes**: their program runs at their turn, in the same task.
- **Live nodes** (`desc.LiveNode`, see [NODE_DEVELOPMENT.md](../NODE_DEVELOPMENT.md)): their `execute` gets and returns any Python object (an image buffer, a `hou.Node`...).
- **A SubGraph** in a subgraph runs in the session of its parent, with its own loop.

Nodes without connections between them can be ordered with flow connections.

**Only what is needed runs**: the nodes without downstream node (and the GraphOutput), and what they read. A node can ignore an input in a context (`desc.BaseNode.ignoredInputs`): `HoudiniScene` ignores its `Scene File` in a Houdini session, so a pipeline node computing the scene path (e.g. `GetCgScene`) is only run in Meshroom and on the farm.

**Scene loads and saves** (Houdini, Maya, Nuke): the task nodes written to load and save the scene themselves keep working as is (`hou.hipFile.load` / `save`, `cmds.file(open=...)` / `cmds.file(save=...)`, `nuke.scriptOpen` / `scriptSave` / `scriptSaveAs`). During a subgraph, loading the scene already open does nothing, and their saves are grouped into one save at the end of a Meshroom task (or at `HoudiniSave`); nothing is saved in a Houdini session unless `HoudiniSave` asks for it. In the session of a software, a node never replaces the open scene (e.g. by loading the last version saved on disk): only a `HoudiniScene` / `MayaScene` / `NukeScene` node set to `sceneFile` opens another one. The Maya nodes written for mayapy can call `maya.standalone.initialize` / `uninitialize`: they do nothing during a subgraph (Maya is already initialized).

Typical Houdini subgraph:
```
GetCgScene -> HoudiniScene -> HoudiniSetFrameRange -> HoudiniUpdateValue -> HoudiniPythonNode -> HoudiniSave
```

### Ports

A new `SubGraph` node contains a `GraphInput` and a `GraphOutput` node (they can be removed). Ports are added, renamed (name and label), reordered or removed like any AnySet child, on either side:
- on the node: connect an attribute to `Inputs` (or `Outputs` to an input), or add one with the **+** button of `Inputs` / `Outputs` in the attribute editor, and the port appears on the `GraphInput` (or `GraphOutput`) of the subgraph — created if it was removed;
- in the subgraph: connect the `Ports` of `GraphInput` / `GraphOutput`, and the node gets the matching `Inputs` / `Outputs` when leaving it.

A port has the type of the attribute connected to it, whatever it is (a `Frame Range` group, a multiple choice such as `Formats`, a list...): in the subgraph, it connects to the attributes of the same type, and the values go through as they are. Connections to the ports of the node are kept. Changing the ports of a node that references a template copies the template into the node (the template file is not changed).

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
| frameRange | runs once per frame of `Frame Range` (`start` to `stop`, included) every `Frame Step` (a fraction of frame for sub-frames, e.g. 0.1); `Frames Per Task` splits the range in tasks (farm), 0 for one task |
| itemList | runs once per item of `Items` (separated by commas or new lines: `mr_001, mr_002`); the item is the `Item` output of `GraphInput` (`ctx.item`), its index `Iteration`; `Frames / Items Per Task` splits the list in tasks |

In a loop, a node runs again at each step only if it depends on the loop: it reads the `iteration` / `frame` of `GraphInput` (or its ports in a count loop), it is a live node (they can read `ctx.frame`; `HoudiniScene` is not), a nested `SubGraph`, or it comes after one of them. The others (e.g. a pipeline node giving the scene, a node setting the frame range) run once, at the first step.

The nodes read the loop state from the outputs of `GraphInput` (live nodes also with `ctx.iteration`, `ctx.frame`); the current frame of Houdini / Maya / Nuke follows the frame loop. A nested `SubGraph` without its own loop sees the frame of its parent.

## User interface

- **Ctrl+G** (or the subgraph button of the bottom-left toolbar of the Graph Editor) puts the selected nodes in a new `SubGraph` node: their connections from other nodes become its inputs, their connections to other nodes its outputs (undoable).
- **Double-click** a `SubGraph` node (or select it and press **I**) to show its subgraph; **U** goes up one level.
- The **breadcrumb** at the top of the Graph Editor shows the path from the project; click an element (or press **U**) to go back. Leaving writes the subgraph back in its node; the ports of the node follow its `GraphInput` / `GraphOutput`.
- **Run Live** (play button of the bar) runs the subgraph now with the inputs of its node: in Meshroom for Python, else in the interpreter of its context, started like the `SubGraph` task (the interpreter of a task node of the subgraph needing the context, in the process environment of its plugin, e.g. its `rez env`), unless `MESHROOM_HYTHON` / `MESHROOM_MAYAPY` / `MESHROOM_NUKE` is set. A frame loop runs its first frame only. The bar shows the result (duration, where it ran, the nodes run and those not needed in this context, the outputs, or the node that failed and its error), and the outline of each node of the subgraph its status: orange while it runs, green when done (its duration in the tooltip), red when it failed (the error in the tooltip), dark red when not run after an error, grey when not needed in this context (e.g. GetCgScene in a session of the software). Run from the project graph, the status is shown on the SubGraph node.
- Saving, computing or submitting from a subgraph acts on the project (the subgraphs are written back first). The undo history is cleared when entering or leaving a subgraph.

## From a software

```python
# Houdini Python shell (Meshroom in PYTHONPATH, MESHROOM_NODES_PATH / MESHROOM_PLUGINS_PATH for other nodes)
import meshroom.subgraph

outputs = meshroom.subgraph.run("/path/houdiniRender.mgt")                       # a template
outputs = meshroom.subgraph.run("/path/project.mg", node="SubGraph_1")           # the subgraph of a project node
outputs = meshroom.subgraph.run("/path/houdiniRender.mgt", frames=(1001, 1010))  # a frame loop
outputs = meshroom.subgraph.run("/path/setup.mgt", items="mr_001, mr_002")      # an item loop
outputs = meshroom.subgraph.run("/path/houdiniRender.mgt", set={"HoudiniSetParms_1.parmPath": "/obj/geo2/tx"})
outputs = meshroom.subgraph.run("/path/feedback.mgt", {"value": 1}, iterations=5)  # GraphInput ports
```

The session of the software is used as it is and prevails: `HoudiniScene` gives the open scene (the nodes computing the scene path for Meshroom are not run), loading the open scene does nothing, nothing is saved unless `HoudiniSave` asks for it, and nothing is closed at the end. `set` changes attribute values without declaring ports. After the first call (loading the node types), a run costs about a millisecond per node plus the work of the nodes.

## Examples

- [subgraph/pythonFeedback.mgt](subgraph/pythonFeedback.mgt): a `LiveScript` in a count loop (no software needed).
- [subgraph/houdiniRender.mgt](subgraph/houdiniRender.mgt): the scene (`HoudiniScene`), parameters, render of the frame of the loop.

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
