# Meshroom Agent Guide

You are assisting on **Meshroom**, a node-based visual programming framework. Use the relative links and directory structure below to orient yourself in the codebase.

Meshroom is a general-purpose Python/QML engine for building, editing, and executing node graphs — it provides a graph editor UI, a node execution engine, and CLI tools, but is domain-agnostic on its own. Concrete functionality is delivered through **plugins** that contribute node types and pipeline templates. Its flagship plugin is **AliceVision**, whose nodes wrap the AliceVision photogrammetry binaries; those C++ computer-vision algorithms live in the separate AliceVision repository, not here.

## Documentation Index

Read the relevant source-of-truth file before working in the area it covers:
* **Project, Concepts & Vocabulary:** [README.md](README.md)
* **Installation & System Setup:** [INSTALL.md](INSTALL.md) — read before touching build, dependency, or environment setup.
* **Plugin Architecture:** [INSTALL_PLUGINS.md](INSTALL_PLUGINS.md) — read before working on plugin loading/packaging.
* **Node Development:** [NODE_DEVELOPMENT.md](NODE_DEVELOPMENT.md) — read before working on node types or their descriptors (`meshroom/nodes/`, `meshroom/core/desc/`).

## Codebase Directory Map

Where this map and the actual tree diverge, trust the tree — then update the map to match (see [Workflow & Delivery](#workflow--delivery)).

```
.
├── .github/                    # CI/CD workflows, issue templates, and automated testing setups
├── .vscode/                    # Shared VS Code debugging and workspace configurations
├── bin/                        # CLI entry points, packaged as executables in setup.py (meshroom_batch,
│                               # meshroom_compute, meshroom_createChunks, meshroom_info, meshroom_newNodeType,
│                               # meshroom_statistics, meshroom_status, meshroom_submit).
│                               # The GUI has NO bin/ script — launch it with ./start.sh (see "Run the app").
├── docker/                     # Dockerfiles for containerized environments (Rocky Linux, Ubuntu, etc.)
├── docs/                       # Documentation resources, developer guides, and illustrations
├── localfarm/                  # Standalone local render-farm daemon (backend/client/launcher); the matching
│                               # submitter lives in meshroom/submitters/localFarm/ (Unix-only, uses fork)
├── meshroom/                   # MAIN SOURCE CODE DIRECTORY
│   ├── common/                 # Qt/headless backend abstraction (BaseObject, models) used across the engine
│   ├── core/                   # Engine logic (Graph, Node, Attribute, execution, (de)serialization)
│   │   └── desc/               # Node/attribute DESCRIPTORS: desc.Node, desc.CommandLineNode, desc.*Param
│   │                           #   (imported as `from meshroom.core import desc`)
│   ├── nodes/                  # Concrete node types, grouped by category (e.g. general/)
│   ├── submitters/             # Built-in render-farm submitters (drive meshroom_submit; e.g. localFarm)
│   ├── ui/                     # User Interface layer (PySide6 / QML-based components)
│   │   ├── qml/                # QML design layouts (GraphEditor, NodeEditor, 3D/2D Viewers, RTI Viewer)
│   │   ├── components/         # Qt helper components exposed to QML (scene3D, scriptEditor, clipboard, ...)
│   │   └── ...                 # Python backends (app.py, graph.py, commands.py, scene.py) binding core to Qt
│   ├── env.py                  # EnvVar registry: MESHROOM_PLUGINS_PATH / NODES_PATH / PIPELINE_TEMPLATES_PATH, etc.
│   └── multiview.py            # Image-extension lists & helpers for building multiview/photogrammetry pipelines
├── tests/                      # Comprehensive suite of unit tests and pipeline validation tests
├── CHANGES.md                  # Changelog tracking features, optimizations, and API breaks
├── CMakeLists.txt              # Build system file for compiling external modules/packaging
├── CONTRIBUTING.md             # Guidelines for developer onboarding and codebase contributions
├── INSTALL.md                  # Detailed steps for building from source and configuring dependencies
└── INSTALL_PLUGINS.md          # Framework documentation explaining how to load custom Python plugins
```

## How It Fits Together (Mental Model)

A few distinctions are easy to confuse. Keep them straight before changing engine code:

* **Descriptor vs. instance.** A *node type* is a **descriptor** class in `meshroom/nodes/<Category>/<Name>.py` that subclasses `desc.Node` (Python-scripted) or `desc.CommandLineNode` (wraps an external command-line program, e.g. an AliceVision tool). The descriptor declares static schema only: `inputs`/`outputs` (lists of `desc.*` attributes such as `desc.File`, `desc.IntParam`, `desc.ChoiceParam`), plus `category`, `documentation`, `size`, and optional `parallelization`. At runtime the engine instantiates it into a live **`Node`** (`meshroom/core/node.py`) whose **`Attribute`** objects (`meshroom/core/attribute.py`) hold the actual values. Rule of thumb: `core/desc/` = schema/definition; `core/node.py` + `core/attribute.py` = live, valued objects.
* **Graph = DAG of attributes.** A **`Graph`** (`meshroom/core/graph.py`) holds nodes connected by **`Edge`**s that link one node's *output* attribute to another node's *input* attribute. A connected input reads its value from upstream; the graph is a DAG and defines evaluation order. Each node computes a content-based **UID** (hash of its inputs) so unchanged nodes can be cached and skipped on recompute.
* **Execution = chunks.** Work is split into **`NodeChunk`**s for parallelism (driven by the descriptor's `size`/`parallelization`). `desc.Node` subclasses implement **`processChunk(chunk)`** in Python; `desc.CommandLineNode` builds a command line from its `commandLine` template plus the chunk's range and runs the external binary. **`TaskManager`** (`meshroom/core/taskManager.py`) orchestrates execution — either **locally** (`compute`) or by **submitting** to a render farm (`submit`) via `meshroom/submitters/`.
* **Persistence.** Graphs are saved as **`.mg`** JSON files (`meshroom/core/graphIO.py`): a versioned `header` plus a `graph` payload. On load, `nodeFactory` reconciles descriptor changes so old projects still open — a node that no longer matches its current descriptor becomes a **`CompatibilityNode`** instead of failing. Pipeline **templates** are just `.mg` files registered at startup.
* **Discovery.** Node types and pipeline templates are loaded at import time (`meshroom/core/__init__.py`, `meshroom/core/plugins.py`) from the built-in `meshroom/nodes/` plus any plugin/template paths (see [INSTALL_PLUGINS.md](INSTALL_PLUGINS.md)).
* **UI bridge.** The engine is Qt-agnostic: `meshroom/common/` selects either a Qt or a headless backend for `BaseObject`, so the core runs without a UI. The `meshroom/ui/*.py` layer wraps it for Qt — `app.py` (application/entry), `graph.py` (a `UIGraph` exposing the core `Graph` as Qt models + async compute), `commands.py` (undo/redo command stack), `scene.py`. QML in `meshroom/ui/qml/` binds to these.

## Development & Verification

* **Supported Python versions:** Target 3.9–3.11. The full test suite runs on **3.11** (Linux + Windows) in CI; `meshroom_compute` (`bin/meshroom_compute`) additionally gets a `-h` smoke test on **3.9**, the minimum supported version. Avoid syntax/features newer than 3.9 in any code reachable from it (`meshroom/core/`, CLI entry points).
* **Lint:** Run `flake8 . --max-line-length=127` locally. CI ([.github/workflows/run-tests.yml](.github/workflows/run-tests.yml)) runs two passes: a **hard-failing** one for real errors (`--select=E9,F63,F7,F82` — syntax/undefined names) and a **non-blocking** style pass (`--exit-zero --max-complexity=10 --max-line-length=127`). Keep both clean; the [Code Style](#code-style) section lists the specific style warnings to avoid.
* **Tests:** `pytest tests/` from the repo root. Add/run targeted tests with `pytest tests/path/to/test_file.py::test_name`.
* **Run the app:** There is no `bin/` script for the GUI. Launch it with `./start.sh` (sets `MESHROOM_ROOT`/`PYTHONPATH`, then runs `python3 meshroom/ui`), or run `python3 meshroom/ui` directly. For headless pipeline runs use `bin/meshroom_batch`. Manually verify UI/pipeline changes this way before reporting them done.

## Code Style

### Python (`meshroom/core/`, `meshroom/core/desc/`, `meshroom/nodes/`, `meshroom/ui/*.py`, `bin/`)

1. **Style Uniformity (Highest Priority):** If an existing file does not perfectly follow PEP 8 or the rules below, **always prefer code uniformity** with the surrounding codebase over strict rule enforcement.

2. **Naming Conventions:** Use **camelCase** for variable names and function/method names (e.g., `myFunction`, `nodeVariable`). Match existing repository naming patterns rather than default PEP 8 snake_case.

3. **Quality Standards (Modified PEP 8):**
   * **Line Length:** Do not apply the PEP 8 79/100 characters-per-line limit. Long lines are acceptable.
   * **Linter Compliance:** Avoid causing these specific issues: `E128` (visual indent), `E222`/`E225` (operator spacing), `E251` (spaces around parameter `=`), `E261` (2 spaces before inline comments), `E275` (space after keyword), `E301`/`E302`/`E303`/`E306` (blank line constraints), `W291`/`W292`/`W293`/`W391` (whitespaces/newlines), `E711`/`E712` (`is None`/`is True`), `F401` (unused imports), `F841` (unused variables), and `F541` (empty f-strings).

4. **Documentation & Comments:**
   * **Functions & Methods:** Every function or method whose purpose is not self-explanatory from its name and signature must include a clear, concise docstring covering its purpose, parameters, and return value. Trivial one-liners and obvious getters/setters may be left undocumented, matching the surrounding file.
   * **Complex Logic:** Add inline comments to explain non-explicit or intricate blocks of code.
   * **Keep it Concise:** Do not over-explain or add redundant descriptions in comments.

5. **Testing:** For changes made to **Core code** (`meshroom/core/`), you must add corresponding unit tests for any new features.

### QML / UI (`meshroom/ui/qml/`)

1. **Style Uniformity:** Match the patterns, indentation, and structure already used in the surrounding `.qml` file.

2. **Naming Conventions:** Use **camelCase** for properties, signals, and functions, consistent with standard QML/JS convention and the existing codebase.

3. **Documentation & Comments:** Same principle as Python — add comments for non-obvious or intricate logic, keep them concise, skip them where the code is self-explanatory.

4. **Testing:** Changes purely to the UI/QML layer do not require unit tests.

## Workflow & Delivery

* Provide only targeted code patches instead of full files.
* Propose changes structured to perform **atomic commits** (one distinct, self-contained change per commit), one feature per PR where possible, per [CONTRIBUTING.md](CONTRIBUTING.md).
* Link the relevant GitHub issue in the PR description, and open it as a draft PR while work is in progress, matching the existing contributor workflow.
* **Keep this file accurate:** whenever a change makes any statement in `AGENTS.md` incorrect or incomplete — a moved/renamed path in the Directory Map, a changed command or CI setting, a shift in the architecture described by the Mental Model — update `AGENTS.md` in the same change so it never drifts from the codebase.
