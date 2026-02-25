# Meshroom Node Development

## Node Creation

This guide shows how to implement three common Meshroom node types: Python-based `Node`, external-executable `CommandLineNode`, and non-computational `InputNode`.

### 1. Node (Python-based)

Use `desc.Node` when your logic runs in Python.
Implement `process(self, node)` to produce outputs.

#### Example: Generate a file

```python
from meshroom.core import desc

class GenerateFile(desc.Node):
    category = "Custom"
    inputs = [
        desc.File(name="input", label="Input", description="", value=""),
        desc.IntParam(name="count", label="Count", description="", value=1),
    ]
    outputs = [
        desc.File(name="output", label="Output", description="", value="{nodeCacheFolder}/out.txt"),
    ]

    def process(self, node):
        # Implement your computation logic here
        with open(node.output.value, "w") as f:
            f.write(f"Processed {node.input.value} ({node.count.value})\n")
```
In this example, the path of the output file is an expression that will always be up-to-date in Meshroom and the corresponding file will be created by the node's computation.

#### Example: Compute values

```
class AddInt(desc.Node):
    category = "Custom"
    inputs = [
        desc.IntParam(name="a", label="Count", description="", value=1),
        desc.IntParam(name="b", label="Count", description="", value=2),
    ]
    outputs = [
        # Dynamic output value
        desc.IntParam(name="outputInt", label="Count", description="", value=None),
    ]

    def process(self, node):
        # Implement your logic here; set output attributes.
        node.outputInt.value = node.a.value + node.b.value
```
In this example, the output param value will ve valid in Meshroom only at the end of the node computation.


### 2. CommandLineNode (external executable)

Use `desc.CommandLineNode` to wrap an external binary. Define a `commandLine` template with `{variable}` placeholders. Meshroom expands it via `buildCommandLine(chunk)` and executes the result [3](#0-2) .

#### Example

```python
from meshroom.core import desc

class MyCmdNode(desc.CommandLineNode):
    commandLine = "mytool --input {inputValue} --output {outputValue}"
    # Optional: range arguments for parallelized nodes
    commandLineRange = "--range {rangeStart} {rangeEnd}"

    inputs = [
        desc.File(name="input", label="Input", description="", value=""),
    ]
    outputs = [
        desc.File(name="output", label="Output", description="", value="{nodeCacheFolder}/out.txt"),
    ]
```

### 3. InputNode (non-computational placeholder)

Use `desc.InputNode` for nodes that only hold data and do not run computation.

#### Example: Input Node

```python
from meshroom.core import desc

class MyInputNode(desc.InputNode):
    category = "Custom"
    inputs = [
        desc.File(name="file", label="File", description="", value=""),
    ]
```

#### Example: Input Node with Initialization

The InitNodes could be combined with `desc.InitNode` to implement `initialize` for command line batching or initialization from drag&drop.

```python
from meshroom.core import desc

class MyInputNode(desc.InputNode, desc.InitNode):
    category = "Custom"
    inputs = [
        desc.File(name="file", label="File", description="", value=""),
    ]

    def initialize(self, node, inputs, recursiveInputs):
        # Populate attributes from command-line inputs.
        if inputs:
            node.file.value = inputs[0]
```

## Attribute Types Available in Meshroom Nodes

Meshroom provides several attribute types you can use in a node’s `inputs` and `outputs`. They are defined in `meshroom.core.desc` and organized into basic parameters, compound containers, geometry helpers, and shape annotations.

### Basic Parameters

| Type | Description | Common Options |
|------|-------------|----------------|
| `BoolParam` | Boolean toggle. | `value` (bool) |
| `IntParam` | Integer with optional range. | `range=(min, max, step)` |
| `FloatParam` | Floating-point with optional range. | `range=(min, max, step)` |
| `StringParam` | Free-form string. | `value` (str) |
| `File` | File or directory path. | `value` (str) |
| `ChoiceParam` | Single or multiple selection from a list. | `values=[...]`, `exclusive` |
| `ColorParam` | RGBA color. | `value` (list/tuple) |
| `PushButtonParam` | Action button in UI; no stored value. | N/A |

### Compound Containers

| Type | Description | Key Args |
|------|-------------|----------|
| `ListAttribute` | Homogeneous list of elements defined by `elementDesc`. | `elementDesc`, `joinChar` |
| `GroupAttribute` | Fixed collection of heterogeneous child attributes (`items`). | `items`, `joinChar` |

Both inherit from `Attribute` and support nesting (lists of groups, groups with lists).

### Geometry Helpers

Convenient groups for 2D geometry, built from `GroupAttribute` and `FloatParam`:

| Type | Fields | Example |
|------|--------|---------|
| `Size2d` | `width`, `height` (float) | `Size2d(name="sz", ..., width=1920, height=1080)` |
| `Vec2d` | `x`, `y` (float) | `Vec2d(name="vec", ..., x=0.0, y=1.0)` |


### Special Properties

- **Name**: Used to access attributes from script.
- **Label**: Label used for the display in the Node Editor.
- **Description**: Tooltip used in the Node Editor.
- **Range constraints**: `IntParam` and `FloatParam` accept `range=(min, max, step)` to bound values.
- **Enabled**: Parameters can be enabled or disabled dynamically (using a lamda).
- **Advanced**: Parameters can be declared as advanced parameters, so they are hidden by default but could be activated in the UI for experts or developpers.
- **Exposed** in the GraphEditor: Files are exposed in the nodal view by default, other type are hidden by default, but it can be defined per attribute.
- **Dynamic outputs**: Set `value=None` in an output attribute to mark it as dynamically computed.
- **Keyable attributes**: Enable per-key values (e.g., per-view) with `keyable=True` and `keyType`. Supported on basic params and shapes.
- **JoinChar**: Controls string serialization for `ListAttribute` and `GroupAttribute` when used in command lines.


### Advanced: Shape Parameters

Used for UI overlays/annotations; they support `keyable` per-view values:

| Type | Description | Example |
|------|-------------|---------|
| `Point2d` | 2D point (`x`, `y`). | `Point2d(name="pt", ...)` |
| `Line2d` | 2D line defined by two points. | `Line2d(name="ln", ...)` |
| `Rectangle` | Axis-aligned rectangle. | `Rectangle(name="rect", ...)` |
| `Circle` | Circle with center and radius. | `Circle(name="c", ...)` |
| `ShapeList` | List of a single shape type (`shape`). | `ShapeList(name="pts", shape=Point2d(...))` |


# Installation

See [INSTALL_PLUGINS.md](./INSTALL_PLUGINS.md)

