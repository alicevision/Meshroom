# Subgraphs

A **subgraph** is a group of nodes run as **one task**, in one context opened once (the current Python, or the session of a software provided by a plugin), the values going from node to node in memory. It looks like a standard Meshroom node (`SubGraph`): on a farm it takes one machine (or one machine per group of frames / items), whatever the number of nodes it contains.

Typical uses:
- a chain of small operations (scripts, conversions, checks) run as one task instead of one task per node;
- the session of a software (from a plugin, see [Contexts](#contexts)): opened once, the nodes change the scene, export or render, then it is closed;
- the same template run from a Python script or the shell of a software, in its session (`meshroom.subgraph.run`).

## Nodes

| Node | Role |
|------|------|
| `SubGraph` | Runs a subgraph as a task (local or farm). Its inputs `ins` are the ports of the `GraphInput` node of the subgraph, its outputs `outs` those of its `GraphOutput` node. |
| `GraphInput` | Entry of the subgraph: one output per port, plus the loop state (`iteration` in a count loop; `frame`, the `frameRange` group (`start`, `stop`) and `frameStep` in a frame range loop; `item` in an item loop). At most one per subgraph. |
| `GraphOutput` | Exit of the subgraph: one input per port. At most one per subgraph, optional. |
| `LiveScript` | Python code run in the context: reads `ins`, `ctx`, `session`; fills `outs`. |

### Any node in a subgraph

A subgraph can contain **any node**, and a node behaves according to where it is: at the top of a project it is a task (its own process, its own farm job); in a subgraph it runs in the process and the context of the subgraph, after the nodes it reads, and its outputs go to the next nodes in memory.
- **Task nodes** (`desc.Node`): their `process` / `processChunk` is called as is, in the process of the subgraph.
- **Command line nodes**: their program runs at their turn, in the same task.
- **Live nodes** (`desc.LiveNode`, see [NODE_DEVELOPMENT.md](../NODE_DEVELOPMENT.md)): their `execute` gets and returns any Python object.
- **A SubGraph** in a subgraph runs in the context of its parent, with its own loop.

Nodes without connections between them can be ordered with flow connections.

**Only what is needed runs**: the nodes without downstream node (and the GraphOutput), and what they read. A node can ignore an input in a context (`desc.BaseNode.ignoredInputs`): e.g. a node giving the scene of a software ignores the path computed by Meshroom when it runs in an open session of that software, so the nodes computing that path are not run there.

### Ports

A new `SubGraph` node contains a `GraphInput` and a `GraphOutput` node (they can be removed). Ports are added, renamed (name and label), reordered or removed like any AnySet child, on either side:
- on the node: connect an attribute to `Inputs` (or `Outputs` to an input), and the port appears on the `GraphInput` (or `GraphOutput`) of the subgraph, created if it was removed;
- in the subgraph: connect the `Ports` of `GraphInput` / `GraphOutput`, and the node gets the matching `Inputs` / `Outputs` when it is left.

A port has the type of the attribute connected to it, whatever it is (a frame range group, a multiple choice, a list...): in the subgraph, it connects to the attributes of the same type, and the values go through as they are. Connections to the ports of the node are kept. Changing the ports of a node that references a template copies the template into the node (the template file is not changed).

### Where the subgraph is stored

- **Embedded** in the node (`Embedded Subgraph`, JSON).
- **Template** (`Template`: a `.mgt`, saved with *File > Save As Template*): used when there is no embedded subgraph. *Make Local* copies the template into the node.

`meshroom.core.subgraph.editing` builds the graph of a subgraph to edit it (`SubGraphStack.enter` / `exit`: the ports of the node follow its `GraphInput` / `GraphOutput` when it is written back) and puts nodes in a new `SubGraph` node (`collapseIntoSubGraph`: their connections from other nodes become its inputs, their connections to other nodes its outputs).

### Contexts

`Context` is where the nodes run: `auto` (the one the nodes need, Python if none), `python`, or a context registered by a plugin. It is opened once for the whole run (all iterations, nested subgraphs) and closed at the end. A live node declares the contexts it can run in (`context`); a task node needs the context whose `executables` contain its `pythonExecutable`.

A plugin registers the context of its software when its modules are imported:

```python
from meshroom.core.subgraph import LiveContext, importable, registerContext


class BlenderContext(LiveContext):
    interpreterVariable = "MESHROOM_BLENDER"   # overrides the interpreter command
    defaultInterpreter = "blender -b --python-exit-code 1 --python"
    executables = ("blender",)                  # task nodes whose pythonExecutable contains it need this context

    @classmethod
    def isAvailable(cls):
        return importable("bpy")

    def open(self):
        import bpy
        super().open()
        self.session = bpy

    def beginStep(self, iteration, frame):
        if frame is not None:
            self.session.context.scene.frame_set(frame)


registerContext("blender", BlenderContext)
```

The nodes reach it with `ctx.context` (`ctx.context.session`). `ownsSession` is True when the run is a task of Meshroom or of a farm (the session can be cleaned in `close`), False from a script or the shell of the software.

### Loops

| Loop | Behaviour |
|------|-----------|
| none | runs once |
| count | `Iterations` runs; the outputs of an iteration feed the inputs of the same name of the next one (a feedback) |
| frameRange | runs once per frame of `Frame Range` (`start` to `stop`, included) every `Frame Step` (a fraction of frame for sub-frames, e.g. 0.1); `Frames / Items Per Task` splits the range in tasks (farm), 0 for one task |
| itemList | runs once per item of `Items` (separated by commas or new lines: `sh010, sh020`); the item is the `Item` output of `GraphInput` (`ctx.item`), its index `Iteration`; `Frames / Items Per Task` splits the list in tasks |

In a loop, a node runs again at each step only if it depends on the loop: it reads the `iteration` / `frame` / `item` of `GraphInput` (or its ports in a count loop), it is a live node with `runsEachStep` (the default: they can read `ctx.frame`), a nested `SubGraph`, or it comes after one of them. The others run once, at the first step. The context follows the frame loop (`LiveContext.beginStep`). A nested `SubGraph` without its own loop sees the frame of its parent.

## User interface

- **Ctrl+G** (or the subgraph button of the bottom-left toolbar of the Graph Editor) puts the selected nodes in a new `SubGraph` node: their connections from other nodes become its inputs, their connections to other nodes its outputs (undoable).
- **Double-click** a `SubGraph` node (or select it and press **I**) to show its subgraph; **U** goes up one level.
- The **breadcrumb** at the top of the Graph Editor shows the path from the project; click an element (or press **U**) to go back. Leaving writes the subgraph back in its node; the ports of the node follow its `GraphInput` / `GraphOutput`. A subgraph whose nodes come from a plugin that is not loaded is not opened (writing it back would lose them).
- The **+** button of `Inputs` / `Outputs` in the attribute editor adds a port by hand (any value, or a typed value shown with its usual editor).
- **Run Live** (play button of the bar) runs the subgraph now with the inputs of its node: in Meshroom when its context is available here, else in the interpreter of its context (`meshroom/core/subgraph/runner.py`). A frame loop runs its first frame only. The bar shows the result (duration, where it ran, the nodes run and those not needed in this context, the outputs, or the node that failed and its error), and the outline of each node of the subgraph its status: orange while it runs, green when done (its duration in the tooltip), red when it failed (the error in the tooltip), dark red when not run after an error, grey when not needed in this context. Run from the project graph, the status is shown on the SubGraph node.
- Saving, computing or submitting from a subgraph acts on the project (the subgraphs are written back first); the title, the save and the cache folder are those of the project. The undo history is cleared when entering or leaving a subgraph (the unsaved changes stay flagged).

## From a script

```python
# Meshroom in PYTHONPATH; MESHROOM_PLUGINS_PATH / MESHROOM_NODES_PATH for the nodes of plugins
import meshroom.subgraph

outputs = meshroom.subgraph.run("/path/template.mgt", {"value": 1})                 # GraphInput ports
outputs = meshroom.subgraph.run("/path/project.mg", node="SubGraph_1")              # the subgraph of a project node
outputs = meshroom.subgraph.run("/path/template.mgt", frames=(1001, 1010))          # a frame loop
outputs = meshroom.subgraph.run("/path/template.mgt", items="sh010, sh020")         # an item loop
outputs = meshroom.subgraph.run("/path/feedback.mgt", {"value": 1}, iterations=5)   # a count loop
outputs = meshroom.subgraph.run("/path/template.mgt", set={"LiveScript_1.code": "outs['x'] = 1"})
```

From the shell of a software, its session is used as it is and prevails, and nothing is closed at the end. `set` changes attribute values without declaring ports; `onNode` reports the status of each node as it runs. The node types are loaded at the first call (again if the plugin variables changed since); after that, a run costs about a millisecond per node plus the work of the nodes.

## Examples

- [subgraph/pythonFeedback.mgt](subgraph/pythonFeedback.mgt): a `LiveScript` in a count loop (no software needed).
