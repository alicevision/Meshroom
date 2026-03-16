# Meshroom Node Development


## Node Creation

This guide shows how to implement three common Meshroom node types: Python-based `Node`, external-executable `CommandLineNode`, and non-computational `InputNode`.

### 1. Node (Pure Python)

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

```python
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

Use `desc.CommandLineNode` to wrap an external binary. Define a `commandLine` template with `{variable}` placeholders. Meshroom expands it via `buildCommandLine(chunk)` and executes the result.

#### Example

```python
from meshroom.core import desc

class MyCmdNode(desc.CommandLineNode):
    commandLine = "mytool --input {inputValue} --output {outputValue}"

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

#### Example: Parameter Types

```python
from meshroom.core import desc

class ParameterTypesSample(desc.Node):
    category = "Custom"
    inputs = [
        desc.BoolParam(name="boolParam", label="Boolean", description="", value=False),
        desc.IntParam(name="intParam", label="Integer", description="", value=10, range=(0, 100, 1)),
        desc.FloatParam(name="floatParam", label="Float", description="", value=3.14, range=(0.0, 10.0, 0.1)),
        desc.StringParam(name="stringParam", label="String", description="", value="default"),
        desc.File(name="fileParam", label="File", description="", value=""),
        desc.ChoiceParam(name="choiceParam", label="Choice", description="", value="opt1", values=["opt1", "opt2", "opt3"], exclusive=True),
        desc.ColorParam(name="colorParam", label="Color", description="", value=[1.0, 0.0, 0.0, 1.0]),
        desc.PushButtonParam(name="buttonParam", label="Button", description=""),
        desc.ListAttribute(
            name="fileList",
            label="File List",
            description="",
            elementDesc=desc.File(name="file", label="File", description="", value=""),
            joinChar=" "
        ),
        desc.GroupAttribute(
            name="inputGroup",
            label="Input Group",
            description="Group with bool, int, string and file",
            items=[
                desc.BoolParam(name="groupBool", label="Boolean", description="", value=True),
                desc.IntParam(name="groupInt", label="Integer", description="", value=42, range=(0, 100, 1)),
                desc.StringParam(name="groupString", label="String", description="", value="groupValue"),
                desc.File(name="groupFile", label="File", description="", value="")
            ]
        )
    ]
    outputs = [
        desc.File(name="outputFile", label="Output File", description="", value="{nodeCacheFolder}/output.txt")
    ]

    def process(self, node):
        with open(node.outputFile.value, "w") as f:
            f.write(f"{node.boolParam.value},{node.intParam.value},{node.floatParam.value},{node.stringParam.value},{node.fileParam.value},{node.choiceParam.value},{node.colorParam.value},{len(node.fileList.value)},{node.inputGroup.groupBool.value},{node.inputGroup.groupInt.value},{node.inputGroup.groupString.value},{node.inputGroup.groupFile.value}\n")
```

### Geometry Helpers

Convenient groups for 2D geometry, built from `GroupAttribute` and `FloatParam`:

| Type | Fields | Example |
|------|--------|---------|
| `Size2d` | `width`, `height` (float) | `Size2d(name="sz", ..., width=1920, height=1080)` |
| `Vec2d` | `x`, `y` (float) | `Vec2d(name="vec", ..., x=0.0, y=1.0)` |


### Attribute Properties

- **Name**: Used to access attributes from script.
- **Label**: Label used for the display in the Node Editor.
- **Description**: Tooltip used in the Node Editor.
- **Range constraints**: `IntParam` and `FloatParam` accept `range=(min, max, step)` to bound values.
- **Enabled**: Parameters can be enabled or disabled dynamically (using a lamda).
- **Advanced**: Parameters can be declared as advanced parameters, so they are hidden by default but could be activated in the UI for experts or developpers.
- **Exposed** in the GraphEditor: Files are exposed in the nodal view by default, other type are hidden by default, but it can be customized per attribute.
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


## Node Descriptor Properties

| Property | Type | Description | Default |
|----------|------|-------------|---------|
| Class documentation | str | Detailed description of the node's purpose | "" |
| `category` | str | Organizational category in the node library | "Other" |
| `cpu` | Level or callable | CPU resource requirement level | Level.NORMAL |
| `ram` | Level or callable | Memory resource requirement level | Level.NORMAL |
| `gpu` | Level or callable | GPU resource requirement level | Level.NONE |
| `size` | Size object | Parallelization size configuration | StaticNodeSize(1) |
| `parallelization` | Parallelization | Chunk division settings | None |

### Example: Basic Node with Properties

```python
class SampleNode(desc.Node):
    """This is the Node documentation that will be available in the Node Editor."""

    category = "Custom Node Category"  # Used in the UI to group nodes in the menu
    size = desc.DynamicNodeSize("inputFiles")  # Size used to define the number of chunks for parallelization

    # Resource levels (`cpu`, `gpu`, `ram`) are used for farm scheduling on suitable hardware
    cpu = Level.NORMAL  # Need standard amount of CPU
    ram = Level.HIGH  # Requires large amount of RAM
    gpu = Level.NONE  # Do not need GPU
```

Resource levels can also be set as callables receiving a node instance, allowing them to be
determined dynamically based on the node's input parameters:

```python
class SampleNode(desc.Node):
    # Dynamically require a GPU based on an input parameter
    gpu = lambda node: desc.Level.INTENSIVE if node.attribute("useGpu").value else desc.Level.NONE
```

The resolved value for a node instance is accessible via the `cpu`, `gpu`, and `ram` properties
on the node object (e.g. `node.cpu`, `node.gpu`, `node.ram`).


## Parallelizing a Node

Meshroom enables node parallelization by splitting work into independent chunks that can be distributed on multiple workstations on compute farm. Configure parallelization by setting `size` and `parallelization` properties on your node descriptor.

### Configuration

#### Size Strategies
- **StaticNodeSize**: Fixed number of tasks
- **DynamicNodeSize**: Size based on an input attribute (list length or linked node size)
- **MultiDynamicNodeSize**: Sum of sizes from multiple input attributes
- **callable**: A callable (e.g. a lambda) receiving the node instance: `lambda node: node.sizeInput.value`

#### Parallelization Settings
Set `parallelization` to control chunk division:
- `blockSize`: Items per chunk
- `staticNbBlocks`: Fixed number of chunks (alternative to blockSize)

### Implementation Examples

#### CommandLineNode with Static Parallelization
```python
class MyParallelCmd(desc.CommandLineNode):
    commandLine = "mytool --input {inputValue} --output {outputValue}"
    commandLineRange = "--range {rangeStart} {rangeEnd}"  # Specific way to precise the range to compute on the command line
    
    size = desc.StaticNodeSize(100)  # 100 items total
    parallelization = desc.Parallelization(blockSize=10)  # 10 chunks of 10 items
```

#### Node with Dynamic Size
```python
class MyParallelNode(desc.Node):
    size = desc.DynamicNodeSize("inputList")  # Size matches list length
    parallelization = desc.Parallelization(blockSize=3)  # Create a chunk every 3 elements in the list
    
    def processChunk(self, chunk):
        # Process chunk.range.iteration
        pass
```

### Range and Chunk Behavior

Each chunk receives a `Range` object with:
- `iteration`: Chunk index
- `start`/`end`: Item indices for this chunk
- `blockSize`: Items per chunk
- `nbBlocks`: Total chunks

For `CommandLineNode`, range placeholders are automatically injected into `commandLineRange` when `node.isParallelized` and `node.size > 1`.


## Installation

See [INSTALL_PLUGINS.md](./INSTALL_PLUGINS.md)

