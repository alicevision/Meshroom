# Meshroom - 3D Reconstruction Software

Meshroom is a Python-based, node-based visual programming framework for 3D reconstruction and computer vision workflows. It provides both a Qt-based GUI application and command-line tools for batch processing.

Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

## Working Effectively

### Bootstrap and Setup
- **Install Python dependencies** (required for all functionality):
  ```bash
  pip install -r requirements.txt
  pip install -r dev_requirements.txt
  ```
  Takes 18 seconds + 10 seconds respectively. Set timeout to 10+ minutes.

- **Install additional CI/development tools**:
  ```bash
  pip install flake8 pytest-cov
  ```

- **Set Python path** (CRITICAL - required for all Python operations):
  ```bash
  export PYTHONPATH=$PWD
  # On Windows: set PYTHONPATH=%CD%
  ```

### Build and Test Process
- **Lint the codebase** (following exact CI process):
  ```bash
  flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
  flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
  ```
  Takes ~1 second each. Set timeout to 5+ minutes. Expect 200+ style warnings (normal).

- **Run unit tests**:
  ```bash
  pytest tests/ -v
  pytest --cov --cov-report=xml --junitxml=junit.xml -v
  ```
  Takes 1.6 seconds (basic) or 3.3 seconds (with coverage). 116 tests should pass. Set timeout to 10+ minutes.

- **Build documentation**:
  ```bash
  cd docs
  pip install -r requirements.txt sphinx-rtd-theme
  sudo apt-get install graphviz  # Linux only
  PYTHONPATH=/path/to/meshroom/root:$PYTHONPATH make html
  ```
  Takes ~31 seconds. Set timeout to 45+ minutes. NEVER CANCEL.

### Running Meshroom Applications

#### GUI Application
```bash
# IMPORTANT: Requires display/EGL libraries and preferably AliceVision
PYTHONPATH=$PWD python meshroom/ui
```
**Note**: Will fail in headless environments with "libEGL.so.1: cannot open shared object file". This is expected.

#### Command Line Tools (VALIDATED - these work without AliceVision)
```bash
# View help for batch processing
PYTHONPATH=$PWD python bin/meshroom_batch --help

# View help for computing existing projects
PYTHONPATH=$PWD python bin/meshroom_compute --help

# Other CLI tools available:
PYTHONPATH=$PWD python bin/meshroom_statistics --help
PYTHONPATH=$PWD python bin/meshroom_status --help
PYTHONPATH=$PWD python bin/meshroom_submit --help
```

#### Package Building
```bash
# Build standalone executables (takes ~2 minutes)
python setup.py build
```
Takes ~2 minutes. Set timeout to 10+ minutes. NEVER CANCEL. Note: built executables may have compatibility issues.

## Validation and Quality Assurance

### Manual Testing Scenarios
After making code changes, always validate with these scenarios:
1. **CLI functionality**: Run `python bin/meshroom_batch --help` and verify help displays correctly
2. **Core imports**: Run `python -c "import meshroom.core; print('Core import successful')"`
3. **Node system**: Run `python -c "import meshroom.core.desc; print('Node system accessible')"`
4. **Test suite**: Run the full pytest suite and ensure all 116 tests pass

### Pre-commit Validation
Always run these commands before committing changes:
```bash
# Lint check (must pass)
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

# Style check (can have warnings)
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

# Unit tests (must pass all 116 tests)
pytest tests/ -v
```

## Dependencies and External Requirements

### Core Python Dependencies (Always Required)
- **Python**: 3.9+ (tested with 3.12.3)
- **PySide6**: 6.8.3 (Qt GUI framework)
- **psutil**: System and process utilities
- **requests**: HTTP library
- **pyseq**: Sequence handling
- **markdown**: Documentation processing

### Optional External Dependencies
- **AliceVision**: 3D reconstruction algorithms (for full functionality)
  - Set `ALICEVISION_ROOT=/path/to/AliceVision/install/directory`
  - Set `MESHROOM_NODES_PATH=${ALICEVISION_ROOT}/share/meshroom`
  - Set `MESHROOM_PIPELINE_TEMPLATES_PATH=${ALICEVISION_ROOT}/share/meshroom`

- **QtAliceVision**: Enhanced GUI features (optional)
  - Set `QML2_IMPORT_PATH=/path/to/QtAliceVision/install/qml`
  - Set `QT_PLUGIN_PATH=/path/to/QtAliceVision/install`

### System Requirements
- **Linux**: Supported (primary platform)
- **Windows**: Supported
- **macOS**: Supported
- **GUI libraries**: libEGL, Qt libraries for full GUI functionality

## Timing Expectations and Timeouts

**CRITICAL**: NEVER CANCEL long-running operations. Use these minimum timeout values:

- **Dependency installation**: 10 minutes (actual: ~30 seconds)
- **Linting**: 5 minutes (actual: ~1 second each)
- **Unit tests**: 10 minutes (actual: ~3 seconds)  
- **Documentation build**: 45 minutes (actual: ~31 seconds)
- **Package building**: 15 minutes (actual: ~2 minutes)
- **AliceVision compilation**: 90+ minutes (if building from source)

## Common Tasks and Workflows

### Repository Structure Reference
```
/home/runner/work/Meshroom/Meshroom/
├── README.md                    # Project overview
├── INSTALL.md                   # Installation guide  
├── CONTRIBUTING.md              # Contribution guidelines
├── requirements.txt             # Runtime dependencies
├── dev_requirements.txt         # Development dependencies
├── setup.py                     # Package configuration
├── meshroom/                    # Main Python package
│   ├── __init__.py             # Package initialization
│   ├── core/                   # Core graph/node system
│   ├── ui/                     # GUI application
│   ├── nodes/                  # Built-in node types
│   └── submitters/             # Render farm integration
├── bin/                        # Command-line tools
│   ├── meshroom_batch          # Batch processing
│   ├── meshroom_compute        # Project computation
│   └── ...                     # Other CLI utilities
├── tests/                      # Unit tests (pytest)
├── docs/                       # Sphinx documentation
└── .github/workflows/          # CI/CD configuration
```

### Environment Variables Reference
```bash
# Essential for development
export PYTHONPATH=$PWD

# For full AliceVision integration
export ALICEVISION_ROOT=/path/to/AliceVision/install
export MESHROOM_NODES_PATH=${ALICEVISION_ROOT}/share/meshroom
export MESHROOM_PIPELINE_TEMPLATES_PATH=${ALICEVISION_ROOT}/share/meshroom

# Optional model paths
export ALICEVISION_SENSOR_DB=${ALICEVISION_ROOT}/share/aliceVision/cameraSensors.db
export ALICEVISION_VOCTREE=${ALICEVISION_ROOT}/share/aliceVision/vlfeat_K80L3.SIFT.tree

# For GUI enhancements
export QML2_IMPORT_PATH=/path/to/QtAliceVision/install/qml
export QT_PLUGIN_PATH=/path/to/QtAliceVision/install
```

## Limitations and Known Issues

### What Works Without AliceVision
- Core Python package imports
- CLI help commands
- Unit testing
- Documentation generation
- Project file creation/manipulation
- Basic node graph operations

### What Requires AliceVision
- Actual 3D reconstruction computation
- Image processing nodes
- Full pipeline execution
- Most template pipelines

### Platform-Specific Notes
- **Linux**: Primary supported platform
- **Windows**: Requires proper PYTHONPATH setup with Windows path syntax
- **Headless environments**: GUI will fail (expected), CLI tools work fine
- **CI environments**: All validation commands work successfully

## Development Best Practices
- Always set `PYTHONPATH=$PWD` before any Python operations
- Run the complete test suite (116 tests) after making changes
- Use the exact CI linting commands to match the build system
- Validate CLI tools functionality as a basic smoke test
- Build documentation to ensure API changes don't break docs generation
- Never assume AliceVision is available - code should gracefully handle its absence