# Meshroom Changelog

For algorithmic changes related to the photogrammetric pipeline, 
please refer to [AliceVision changelog](https://github.com/alicevision/AliceVision/blob/develop/CHANGES.md).

## Meshroom 2025.1.0 (2025/08/13)

Meshroom has now become a node-based visual programming toolbox for creating, managing, and executing complex data processing pipelines, with a new plugin architecture.
Standard computer vision pipelines such as photogrammetry, camera tracking, HDR panorama, Lidar Meshing, Raw image files conversion and color calibration are now unified within the AliceVision plugin, featuring numerous improvements and optimizations.
Additionally, new AI-powered capabilities include a semantic segmentation plugin and a collection of open-source extensions available via the new MeshroomHub: https://github.com/meshroomHub. This platform enables Gaussian Splatting, monocular depth estimation, and other exploratory features, welcoming developer contributions to expand and enhance these capabilities for upcoming releases.

### Highlights

#### Meshroom New Features

- **Advanced Plugin Architecture**: Dedicated sub-process isolation for Python nodes with independent local environments
- **Integrated Development Tools**:
  - Built-in Python script editor
  - Node’s source code hot-reload for rapid node development iterations
- **Enhanced GraphEditor**:
  - Dynamic output attributes enabling new workflow usages
  - New InputNode type enabling interactive evaluation without explicit computation
  - Multiple edge disconnection methods and node colorization for better user experience
  - Node notifications to attribute changes
- **Enhanced 2D Viewer**:
  - Initial timeline integration with sequence playback controls
  - New Reflectance Transformation Imaging (RTI) Viewer: Interactive visualization of albedo and normal maps with real-time lighting control
  - New Home Page: featuring pipeline templates and quick access to recent projects.

#### AliceVision Plugin New Features

- New Pipelines
  - **Color Calibration**: Automated color correction from color charts
  - **Raw to EXR conversion**: Professional image format processing
  - **Object Reconstruction**: Targeted reconstruction with automatic object segmentation
  - **Turntable Object Reconstruction**: Streamlined workflow for rotating object capture
  - **360° Object Reconstruction**: Reconstruction of complete dual-sided scanning
  - **LiDAR Processing**: Native E57 file import with integrated mesh generation
  - **Multi-View Photometric Stereo**: Advanced surface detail reconstruction with multiple light sources for each viewpoint.
- Pipelines Improvements
  - **Camera Tracking pipeline**: improved stability and reliability
  - **Introduced experimental fine-grained pipelines** for increased modularity and workflow flexibility
- Core Enhancements
  - **Python Bindings Integration**: Enhanced AliceVision accessibility with native Python support for streamlined Machine Learning workflows

#### New MrSegmentation Plugin

AI segmentation nodes that identify and isolate image objects using natural language prompts, enabling intuitive content-aware processing through foundation models.

#### MeshroomHub Plugins

New exploratory Machine Learning plugins on [MeshroomHub](github.com/meshroomHub):
- mrGSplat: Gaussian Splat optimization and rendering
- mrDepthEstimation: Monocular depth inference
- mrDenseMotion: Optical flow estimation
- mrRoma: Dense deep feature matching
- mrIntrinsicImageDecomposition: Albedo, normals, and material extraction
- mrDeblurring: Video deblurring
- mrGeolocation: GPS extraction and geographic models download

Based on [AliceVision 3.3.0](https://github.com/alicevision/AliceVision/tree/v3.3.0).

### Major Features

- Add an "E57" importer node [PR](https://github.com/alicevision/Meshroom/pull/2308)
- First node for Lidar Meshing [PR](https://github.com/alicevision/Meshroom/pull/2324)
- New InputNode for nodes without computation and support for all param types in output (and no more limited to File type) [PR](https://github.com/alicevision/Meshroom/pull/2364)
- [core] New dynamic output attributes [PR](https://github.com/alicevision/Meshroom/pull/2432)
- First Homepage [PR](https://github.com/alicevision/Meshroom/pull/2452)
- Qt6.6.3 / PySide6.6.3.1 upgrade [PR](https://github.com/alicevision/Meshroom/pull/2599)
- New MultiView Photometric Stereo pipeline and new sfmFilter node [PR](https://github.com/alicevision/Meshroom/pull/2582)
- [ui] Python Script Editor Improvements [PR](https://github.com/alicevision/Meshroom/pull/2587)
- New local isolated computation for python nodes [PR](https://github.com/alicevision/Meshroom/pull/2703)
- New Plugin Architecture for Node Registration [PR](https://github.com/alicevision/Meshroom/pull/2733)
- [ui]: Introduction of multiple ways to remove Node Edges [PR](https://github.com/alicevision/Meshroom/pull/2644)
- [core] Runtime-specific environments support [PR](https://github.com/alicevision/Meshroom/pull/2747)
- [Photometric Stereo] MultiView fusion in Texturing [PR](https://github.com/alicevision/Meshroom/pull/2243)
- Add a Python ScriptEditor in the GraphEditor tab [PR](https://github.com/alicevision/Meshroom/pull/2456)

### Features

- Custom loader for .pc.ply point clouds [PR](https://github.com/alicevision/Meshroom/pull/2346)
- Lidar nodes [PR](https://github.com/alicevision/Meshroom/pull/2365)
- [ui] Viewer2D: Display lighting circle with auto detected sphere [PR](https://github.com/alicevision/Meshroom/pull/2413)
- [ui] RGBA shortcuts for Image Viewer [PR](https://github.com/alicevision/Meshroom/pull/2425)
- [ui] Shortcuts in Viewer2D and SequencePlayer [PR](https://github.com/alicevision/Meshroom/pull/2430)
- [ui] node time computation and chunks count in node editor header [PR](https://github.com/alicevision/Meshroom/pull/1867)
- [core/ui] Load image sequence from node's output in SequencePlayer [PR](https://github.com/alicevision/Meshroom/pull/2375)
- [core] Forward the onAttributeChanged notification to all linked attributes [PR](https://github.com/alicevision/Meshroom/pull/2453)
- add 3de undistortion models [PR](https://github.com/alicevision/Meshroom/pull/2446)
- [GraphEditor] Base `ChoiceParam` model on attribute instead of description [PR](https://github.com/alicevision/Meshroom/pull/2494)
- [core] Reference the attribute's instance type in its description [PR](https://github.com/alicevision/Meshroom/pull/2493)
- [ui] Improve command line help message [PR](https://github.com/alicevision/Meshroom/pull/2518)
- Added Pre and Post process functions on the Base Node [PR](https://github.com/alicevision/Meshroom/pull/2539)
- [ui] Add and improve multiple UI tools for Photometric stereo [PR](https://github.com/alicevision/Meshroom/pull/2444)
- Refactor Node selection for better UX and performance [PR](https://github.com/alicevision/Meshroom/pull/2605)
- New SfMColorizing Node [PR](https://github.com/alicevision/Meshroom/pull/2610)
- Update sfm pipeline to accept meshes [PR](https://github.com/alicevision/Meshroom/pull/2642)
- Enable Fitting of selected Nodes in the Graph Editor when Fit is invoked  [PR](https://github.com/alicevision/Meshroom/pull/2652)
- Add relative paths to nodes as variables [PR](https://github.com/alicevision/Meshroom/pull/2629)
- Node to inject survey points in the SFM [PR](https://github.com/alicevision/Meshroom/pull/2696)
- [ui] AttributeEditor: Feature/attribute navigation buttons [PR](https://github.com/alicevision/Meshroom/pull/2716)
- [ui] Homepage: Project can be removed with right click [PR](https://github.com/alicevision/Meshroom/pull/2724)
- [ui] Viewer2D: Add the pixel (x,y) values in the toolbar (editable) [PR](https://github.com/alicevision/Meshroom/pull/2723)
- [ui] AttributeEditor: Allow displaying attibute in corresponding viewport  [PR](https://github.com/alicevision/Meshroom/pull/2722)
- Update to Qt/PySide 6.8.3 [PR](https://github.com/alicevision/Meshroom/pull/2692)
- Add a "ConvertDistortion" node [PR](https://github.com/alicevision/Meshroom/pull/2353)
- [ui] Sync SequencePlayer and Viewer3D [PR](https://github.com/alicevision/Meshroom/pull/2360)
- Viewer3D: Adjust bounding-box by moving faces [PR](https://github.com/alicevision/Meshroom/pull/2385)
- [core/ui] Add support for PushButton attribute [PR](https://github.com/alicevision/Meshroom/pull/2382)
- First version of For Loop implementation [PR](https://github.com/alicevision/Meshroom/pull/2504)
- Generate depthmaps from sfmData and mesh [PR](https://github.com/alicevision/Meshroom/pull/2556)
- [ui] Use the improved Sequence Player and enable it by default [PR](https://github.com/alicevision/Meshroom/pull/2557)
- [AttributePin] Add tooltip to display type of attribute [PR](https://github.com/alicevision/Meshroom/pull/2527)
- [core/ui] "Exposed" property added to attributeDesc [PR](https://github.com/alicevision/Meshroom/pull/2528)
- Extract more metadata using exifTool [PR](https://github.com/alicevision/Meshroom/pull/2645)
- Add equirectangular camera model in `CameraInit` [PR](https://github.com/alicevision/Meshroom/pull/2630)
- Fix: Improve large project file loading performance [PR](https://github.com/alicevision/Meshroom/pull/2665)
- UI: Redesign ChoiceParam UI component [PR](https://github.com/alicevision/Meshroom/pull/2656)
- Create new pipeline for testing modular sfm [PR](https://github.com/alicevision/Meshroom/pull/2664)
- [ui] Graph Editor Update: Quick Node Coloring with the Color Selector Tool [PR](https://github.com/alicevision/Meshroom/pull/2604)
- [doc] README.md: Add DeepWiki link, the AI documentation you can talk to [PR](https://github.com/alicevision/Meshroom/pull/2792)

### Other Improvements

- Start Development 2024.1.0 [PR](https://github.com/alicevision/Meshroom/pull/2268)
- ImageSegmentation: add an option to choose between cpu and gpu [PR](https://github.com/alicevision/Meshroom/pull/2267)
- [Viewer] Display error labels when an image cannot be loaded [PR](https://github.com/alicevision/Meshroom/pull/2250)
- [MaterialIcons] Add script to generate the list of available MaterialIcons and update it [PR](https://github.com/alicevision/Meshroom/pull/2247)
- Add option to keep input filename in imageSegmentation [PR](https://github.com/alicevision/Meshroom/pull/2288)
- Add camera color spaces [PR](https://github.com/alicevision/Meshroom/pull/2251)
- [docker] Fix link to download `libassimpsceneimport.so` in Docker images [PR](https://github.com/alicevision/Meshroom/pull/2310)
- Added PLY to list of supported files in 3D viewer [PR](https://github.com/alicevision/Meshroom/pull/2316)
- E57 importer is now generating multiple sfmData [PR](https://github.com/alicevision/Meshroom/pull/2318)
- Added semantic logic to display multiple 3d objects [PR](https://github.com/alicevision/Meshroom/pull/2320)
- [submitters] Update SimpleFarm configuration tags [PR](https://github.com/alicevision/Meshroom/pull/2348)
- [ui] drag&drop: common behavior for graph editor and image gallery [PR](https://github.com/alicevision/Meshroom/pull/2342)
- [core] Add new type of ChoiceParam that changes dynamically [PR](https://github.com/alicevision/Meshroom/pull/2350)
- [ui] Add new FilterComboBox for ChoiceParam attributes [PR](https://github.com/alicevision/Meshroom/pull/2358)
- [core/ui] Hide output attributes flagged for visualisation [PR](https://github.com/alicevision/Meshroom/pull/2369)
- Update ripple constraints [PR](https://github.com/alicevision/Meshroom/pull/2374)
- Hide disabled File attributes and their connections [PR](https://github.com/alicevision/Meshroom/pull/1925)
- [ui] Sequence Player UX improvements (fps, slider, frame) [PR](https://github.com/alicevision/Meshroom/pull/2362)
- [core] BugFix : Upgrade of Dynamic Choice Param fixed [PR](https://github.com/alicevision/Meshroom/pull/2380)
- [ui] Bounding Box are usable in other nodes, not only Meshing [PR](https://github.com/alicevision/Meshroom/pull/2391)
- [ui] Cut option available in GraphEditor [PR](https://github.com/alicevision/Meshroom/pull/2399)
- [core] Set internal attributes when copy/pasting nodes [PR](https://github.com/alicevision/Meshroom/pull/2390)
- [ImageGallery] Display CameraInit label and defaultLabel to avoid confusion [PR](https://github.com/alicevision/Meshroom/pull/2383)
- [GraphEditor] Internal Custom Color Picker disabled when node is locked [PR](https://github.com/alicevision/Meshroom/pull/2384)
- Bump requests from 2.27.1 to 2.32.0 [PR](https://github.com/alicevision/Meshroom/pull/2405)
- [ui] Selected node header set to base color [PR](https://github.com/alicevision/Meshroom/pull/2401)
- [ui] Remove intrinsic if not used by any viewpoint [PR](https://github.com/alicevision/Meshroom/pull/2395)
- [ui] Right click on text element in AttributeEditor open Copy/Paste menu [PR](https://github.com/alicevision/Meshroom/pull/2366)
- [ui] Fix BoundingBox visibility icon because of mapping name [PR](https://github.com/alicevision/Meshroom/pull/2386)
- Add track coordinates [PR](https://github.com/alicevision/Meshroom/pull/2406)
- [ui] Conversion of relative paths to absolute ones [PR](https://github.com/alicevision/Meshroom/pull/2412)
- [core] Compare last saved date before saving to prevent overwrite [PR](https://github.com/alicevision/Meshroom/pull/2414)
- Fix 3D Viewer zooming problem [PR](https://github.com/alicevision/Meshroom/pull/2379)
- [ui] Use ExportAnimatedCamera output for image overlay in Viewer3D [PR](https://github.com/alicevision/Meshroom/pull/2398)
- [GraphEditor] Eye on displayable node even if not computed [PR](https://github.com/alicevision/Meshroom/pull/2427)
- [ui] Add "large" option to multiline string param [PR](https://github.com/alicevision/Meshroom/pull/2437)
- [ui] Auto Update CameraInit when displaying node [PR](https://github.com/alicevision/Meshroom/pull/2431)
- Fix compatibility upgrade issue [PR](https://github.com/alicevision/Meshroom/pull/2436)
- Depth map filter: display normals if enabled [PR](https://github.com/alicevision/Meshroom/pull/2442)
- [ui] do not use native dialog [PR](https://github.com/alicevision/Meshroom/pull/2439)
- File export ordering [PR](https://github.com/alicevision/Meshroom/pull/2440)
- [SequencePlayer] Fetching option added [PR](https://github.com/alicevision/Meshroom/pull/2415)
- Provide access to the current frame from the graph [PR](https://github.com/alicevision/Meshroom/pull/2443)
- Update ripple with "cuda" instead of "gpu" [PR](https://github.com/alicevision/Meshroom/pull/2448)
- Provide access to the path of the currently displayed frame [PR](https://github.com/alicevision/Meshroom/pull/2449)
- [Viewer] Fix all QML errors on the Sequence Player [PR](https://github.com/alicevision/Meshroom/pull/2451)
- Remove plugin loading from core __init__ [PR](https://github.com/alicevision/Meshroom/pull/2458)
- [ui] Sequence Player UI Modifications [PR](https://github.com/alicevision/Meshroom/pull/2445)
- [ui] Add MESHROOM_USE_SEQUENCE_PLAYER environment variable [PR](https://github.com/alicevision/Meshroom/pull/2463)
- Display ION container version in Meshroom  [PR](https://github.com/alicevision/Meshroom/pull/2468)
- Compute or Submit selected nodes [PR](https://github.com/alicevision/Meshroom/pull/2459)
- Add new SfMExpanding node [PR](https://github.com/alicevision/Meshroom/pull/2416)
- Add squeeze option [PR](https://github.com/alicevision/Meshroom/pull/2466)
- [Viewer] Current frame for Sequence should not be set during changes of Image Gallery [PR](https://github.com/alicevision/Meshroom/pull/2472)
- Remove some computers even for normal tasks [PR](https://github.com/alicevision/Meshroom/pull/2479)
- [GraphEditor] Implementation of Recompute Button [PR](https://github.com/alicevision/Meshroom/pull/2473)
- [core] Attribute: Directly access description's type in `getType()` [PR](https://github.com/alicevision/Meshroom/pull/2490)
- [Viewer] Update error values for QtAV's `EStatus` enum [PR](https://github.com/alicevision/Meshroom/pull/2491)
- [GraphEditor] Improve visibility of chunks in progress bar [PR](https://github.com/alicevision/Meshroom/pull/2507)
- [ui] Correctly lose focus on `StringParam` when clicking outside of its text field [PR](https://github.com/alicevision/Meshroom/pull/2512)
- Multiple shots: Align and merge multiple SfM from feature matches [PR](https://github.com/alicevision/Meshroom/pull/2484)
- Homepage Quick Adjustments [PR](https://github.com/alicevision/Meshroom/pull/2520)
- Add locks for intrinsics [PR](https://github.com/alicevision/Meshroom/pull/2517)
- sfmTransform: Add option to lineup camera motion with object/lidar given an external camera pose [PR](https://github.com/alicevision/Meshroom/pull/2524)
- [ui] Open project from browser in homepage & quick adjustments [PR](https://github.com/alicevision/Meshroom/pull/2525)
- [ui] Minor UI modifications [PR](https://github.com/alicevision/Meshroom/pull/2530)
- [ui] Fix click on Category in Node Menu to keep the nodes displayed [PR](https://github.com/alicevision/Meshroom/pull/2526)
- [core] Simplify attribute invalidation in nodes' descriptions [PR](https://github.com/alicevision/Meshroom/pull/2523)
- UI Changes [PR](https://github.com/alicevision/Meshroom/pull/2531)
- [AttributeItemDelegate] Position the attribute description tooltip [PR](https://github.com/alicevision/Meshroom/pull/2532)
- [ui] Add View Image Gallery Parameter [PR](https://github.com/alicevision/Meshroom/pull/2541)
- [core] Simplify node descriptions [PR](https://github.com/alicevision/Meshroom/pull/2538)
- Use export distortion and new segmentation node in templates [PR](https://github.com/alicevision/Meshroom/pull/2549)
- Add wireframe for Qt6 [PR](https://github.com/alicevision/Meshroom/pull/2561)
- Change picking behavior for qt6 upgrade [PR](https://github.com/alicevision/Meshroom/pull/2564)
- [qt6] Fix 8Bits image viewer zoom/fit [PR](https://github.com/alicevision/Meshroom/pull/2565)
- [blender] Adapt `ScenePreview`'s Blender script to pixel ratio [PR](https://github.com/alicevision/Meshroom/pull/2572)
- Update panorama display [PR](https://github.com/alicevision/Meshroom/pull/2573)
- Fix attribute value change propagation and callback handling [PR](https://github.com/alicevision/Meshroom/pull/2586)
- Tracking pipelines segmentation update [PR](https://github.com/alicevision/Meshroom/pull/2583)
- [qt6]|Viewer3D] Fix mouse for camera controller [PR](https://github.com/alicevision/Meshroom/pull/2566)
- Discard attribute changed callbacks during graph loading [PR](https://github.com/alicevision/Meshroom/pull/2598)
- Split `meshroom.core.desc` module into a package with submodules [PR](https://github.com/alicevision/Meshroom/pull/2592)
- [ui] Minor UI stabilization fixes for Qt 6 [PR](https://github.com/alicevision/Meshroom/pull/2606)
- [ui] Fix field of view functions for tall images [PR](https://github.com/alicevision/Meshroom/pull/2609)
- [Viewer3D] Apply the pixel aspect ratio for the Frame Overlay [PR](https://github.com/alicevision/Meshroom/pull/2533)
- [ui] Improve Search Bar component [PR](https://github.com/alicevision/Meshroom/pull/2581)
- [BugFix] File save dialog now requires a valid filename [PR](https://github.com/alicevision/Meshroom/pull/2602)
- [GraphEditor] AttributeItemDelegate: Use MaterialLabel for uncomputed attributes [PR](https://github.com/alicevision/Meshroom/pull/2616)
- CI: add codecov [PR](https://github.com/alicevision/Meshroom/pull/2618)
- Sfm Bootstraping parameterization [PR](https://github.com/alicevision/Meshroom/pull/2619)
- Fix Qt6-induced issues [PR](https://github.com/alicevision/Meshroom/pull/2620)
- [ui] GraphEditor: Address Key Event Conflicts in Node Menu [PR](https://github.com/alicevision/Meshroom/pull/2622)
- [ui] Add Validation for Save file path accessibility [PR](https://github.com/alicevision/Meshroom/pull/2625)
- [ui] NodeEditor: Addressed Tab Retention when switching Node selection [PR](https://github.com/alicevision/Meshroom/pull/2624)
- Add support for QML debugging/profiling [PR](https://github.com/alicevision/Meshroom/pull/2623)
- [GraphEditor] Fix injections into signal handlers with JS functions [PR](https://github.com/alicevision/Meshroom/pull/2627)
- [ui] "About" dialog: Fix some display issues [PR](https://github.com/alicevision/Meshroom/pull/2640)
- Update version number and copyrights [PR](https://github.com/alicevision/Meshroom/pull/2639)
- SelectionBox: Fixed the offset on the selection box highlight appearing in the Graph Editor when dragging to select Nodes [PR](https://github.com/alicevision/Meshroom/pull/2647)
- [ui] Moved Auto-Layout Depth Settings under Graph Editor Menu [PR](https://github.com/alicevision/Meshroom/pull/2646)
- Enable merge of multiple sfmDatas [PR](https://github.com/alicevision/Meshroom/pull/2654)
- [ui][fix] Edge: Fixing an issue with mouse event on Custom EdgeMouseArea causing Crash [PR](https://github.com/alicevision/Meshroom/pull/2650)
- [ui] Refactor the access to the list of recent project files [PR](https://github.com/alicevision/Meshroom/pull/2637)
- Mask processing node [PR](https://github.com/alicevision/Meshroom/pull/2658)
- Export Maya .mel Script  [PR](https://github.com/alicevision/Meshroom/pull/2617)
- Refactor Graph de/serialization [PR](https://github.com/alicevision/Meshroom/pull/2612)
- Node: Propagate attribute change via `valueChanged` signal [PR](https://github.com/alicevision/Meshroom/pull/2657)
- [qml] Fix QML warnings related to chunks [PR](https://github.com/alicevision/Meshroom/pull/2673)
- Add maya scene export [PR](https://github.com/alicevision/Meshroom/pull/2674)
- NodeAPI: Trigger node creation callback only for explicit new node creation [PR](https://github.com/alicevision/Meshroom/pull/2671)
- [ui] app: Register components to QML before instantiating the engine [PR](https://github.com/alicevision/Meshroom/pull/2676)
- [ui] Application: fix save-as dialog not working properly (Qt6.7+) [PR](https://github.com/alicevision/Meshroom/pull/2683)
- [GraphEditor] Only display "Pipelines" menu when templates are available [PR](https://github.com/alicevision/Meshroom/pull/2678)
- [qml] Fix QML warnings when dropping project files into the Graph Editor [PR](https://github.com/alicevision/Meshroom/pull/2680)
- Export USD Node [PR](https://github.com/alicevision/Meshroom/pull/2667)
- [ui] AttributeEditor: Generic TextField param editor improvements [PR](https://github.com/alicevision/Meshroom/pull/2686)
- ChoiceParam: add option to serialize overriden values [PR](https://github.com/alicevision/Meshroom/pull/2682)
- [core] Node: Status should be `NONE` when there is no chunk [PR](https://github.com/alicevision/Meshroom/pull/2695)
- Move nodes and templates to AliceVision's repository [PR](https://github.com/alicevision/Meshroom/pull/2697)
- Remove internal and no longer used files [PR](https://github.com/alicevision/Meshroom/pull/2711)
- Modernize to python 3.9 using flynt and pyupgrade [PR](https://github.com/alicevision/Meshroom/pull/2710)
- [doc] README: Clarified distinction between Meshroom engine, user interface, and plugins [PR](https://github.com/alicevision/Meshroom/pull/2718)
- Use shutil to load nvidia-smi [PR](https://github.com/alicevision/Meshroom/pull/2721)
- [ui] Viewer2D can display the content of tracks files [PR](https://github.com/alicevision/Meshroom/pull/2720)
- [ui] [fix] Attribute: Fix the qml warnings on intrisincs [PR](https://github.com/alicevision/Meshroom/pull/2739)
- [ui] Application: Use CamelCase and disable tooltips when menus are disabled [PR](https://github.com/alicevision/Meshroom/pull/2742)
- ListAttribute: fix methods not considering connected attribute's value [PR](https://github.com/alicevision/Meshroom/pull/2660)
- [fix] remove targetSize in viewer2d which was removed in qtAliceVision [PR](https://github.com/alicevision/Meshroom/pull/2746)
- [ui] Homepage: Update logos of sponsors [PR](https://github.com/alicevision/Meshroom/pull/2729)
- [ui] Rework of MessageDialog for CompatibilityManager and SensorDBDialog [PR](https://github.com/alicevision/Meshroom/pull/2537)
- [qml] Fix some minor QML warnings [PR](https://github.com/alicevision/Meshroom/pull/2756)
- Add support for `ALICEVISION_LIBPATH` environment variable [PR](https://github.com/alicevision/Meshroom/pull/2757)
- [docker] minor updates [PR](https://github.com/alicevision/Meshroom/pull/2765)
- [core] plugins: Add support for virtual environments on Windows [PR](https://github.com/alicevision/Meshroom/pull/2768)
- [core] Adding rangeBlocksCount to `Parallelization` [PR](https://github.com/alicevision/Meshroom/pull/2767)
- Bump requests from 2.32.0 to 2.32.4 [PR](https://github.com/alicevision/Meshroom/pull/2743)
- Fix colorHueComponent slider background [PR](https://github.com/alicevision/Meshroom/pull/2788)
- [core] plugins: Look recursively for "lib" directories in Linux venv [PR](https://github.com/alicevision/Meshroom/pull/2777)
- [core] plugins: Virtual environments should be named "venv" instead of having the plugin's name [PR](https://github.com/alicevision/Meshroom/pull/2793)
- [qml] Minor UI fixes [PR](https://github.com/alicevision/Meshroom/pull/2783)
- [qml] Use native FileDialogs [PR](https://github.com/alicevision/Meshroom/pull/2784)
- Set the default environment variables for the color chart detection models [PR](https://github.com/alicevision/Meshroom/pull/2796)
- [ui] Remove the `Live Reconstruction` and `Augment Reconstruction` features [PR](https://github.com/alicevision/Meshroom/pull/2786)
- Improve behaviour when dropping folders [PR](https://github.com/alicevision/Meshroom/pull/2797)
- [core] plugins: Load plugin's configuration file upon its initialisation [PR](https://github.com/alicevision/Meshroom/pull/2778)
- [core] plugins: Downgrade the log level when loading the config file [PR](https://github.com/alicevision/Meshroom/pull/2798)

### Bugfixes

- Fix duplicated icon in MaterialIcons [PR](https://github.com/alicevision/Meshroom/pull/2277)
- Correctly delete thread pools when exiting Meshroom with Python 3.9 [PR](https://github.com/alicevision/Meshroom/pull/2286)
- [Viewer] Viewer: Fix various issues with the 2D Viewer [PR](https://github.com/alicevision/Meshroom/pull/2283)
- Use the correct response file to display the graph of the Camera Response Function [PR](https://github.com/alicevision/Meshroom/pull/2282)
- Update `ListAttributes` identically when removing edges or nodes [PR](https://github.com/alicevision/Meshroom/pull/2280)
- Upgrade intrinsics for distortion [PR](https://github.com/alicevision/Meshroom/pull/2349)
- [ui] Correctly display images from node outputs even if there is no `CameraInit` node [PR](https://github.com/alicevision/Meshroom/pull/2363)
- [ui] Scroll available in FilterComboBox [PR](https://github.com/alicevision/Meshroom/pull/2376)
- [Viewer] fix lens distortion viewer status when switching between projects [PR](https://github.com/alicevision/Meshroom/pull/2377)
- [ui] Fix drag and drop of heavy number of frames [PR](https://github.com/alicevision/Meshroom/pull/2378)
- SequencePlayer: Forbid "selecting" an invalid frame number [PR](https://github.com/alicevision/Meshroom/pull/2388)
- [ui] Prevent Feature Points to display on external images [PR](https://github.com/alicevision/Meshroom/pull/2389)
- [ui/core] Fix get latest SfM node for previz [PR](https://github.com/alicevision/Meshroom/pull/2396)
- [nodes/ui] Fix ExportAnimatedCamera outputs for ScenePreview use [PR](https://github.com/alicevision/Meshroom/pull/2420)
- [fix] Various fixes [PR](https://github.com/alicevision/Meshroom/pull/2419)
- Prevent updates of the latest SfM node when the graph's topology is dirty [PR](https://github.com/alicevision/Meshroom/pull/2435)
- [Utils] `getTimeStr`: Round up the number of minutes correctly [PR](https://github.com/alicevision/Meshroom/pull/2254)
- [ui] Graph: Connect all chunks when setting a graph for the first time [PR](https://github.com/alicevision/Meshroom/pull/2454)
- [core] Exclude edges from `InputNode` nodes in `dfsToProcess` [PR](https://github.com/alicevision/Meshroom/pull/2455)
- [core] Values of ChoiceParam should be a list, Error message added for initialisation [PR](https://github.com/alicevision/Meshroom/pull/2469)
- Some fixes for dynamic output attributes [PR](https://github.com/alicevision/Meshroom/pull/2470)
- [ui] Fix local computation of subgraphs for unsaved projects [PR](https://github.com/alicevision/Meshroom/pull/2471)
- [ui] Fix Camera Init Group Index should stay the same at adding or removing CameraInit events [PR](https://github.com/alicevision/Meshroom/pull/2474)
- [Viewer2D] Only reset index of currentFrame if the currentFrame is after max of frameRange [PR](https://github.com/alicevision/Meshroom/pull/2480)
- [ui] setSfm only depends on nodes with category "sfm" and CameraInit should be set only if it is different from the current one [PR](https://github.com/alicevision/Meshroom/pull/2476)
- [GraphEditor] AttributeItemDelegate: Return valid component for `PushButton` [PR](https://github.com/alicevision/Meshroom/pull/2482)
- Initialize `core` plugins at different moments [PR](https://github.com/alicevision/Meshroom/pull/2487)
- [ui] app: Correctly reload list of available templates [PR](https://github.com/alicevision/Meshroom/pull/2499)
- [core] Catch exception for calls to optional descriptor method on node creation [PR](https://github.com/alicevision/Meshroom/pull/2500)
- [ui] Improve sequence display [PR](https://github.com/alicevision/Meshroom/pull/2502)
- [ui] GraphEditor.newNodeMenu: fix unstable menu height [PR](https://github.com/alicevision/Meshroom/pull/2511)
- [ui] Add proper distinction between the main window and the application [PR](https://github.com/alicevision/Meshroom/pull/2521)
- [ui] Fix function evaluations in invalid QML context and minor fixes [PR](https://github.com/alicevision/Meshroom/pull/2519)
- Fix Several Compatibility Nodes Operations [PR](https://github.com/alicevision/Meshroom/pull/2506)
- [main] Fix imagesFolder variable in order to save when gallery is not empty [PR](https://github.com/alicevision/Meshroom/pull/2535)
- [bin] Import correct `Graph` objects for `meshroom_batch` [PR](https://github.com/alicevision/Meshroom/pull/2536)
- Fix homepage SplitViews [PR](https://github.com/alicevision/Meshroom/pull/2545)
- [core] Check provided template folder exists before attempting to load it [PR](https://github.com/alicevision/Meshroom/pull/2552)
- [img] Remove incorrect sRGB profile from UiO logo [PR](https://github.com/alicevision/Meshroom/pull/2555)
- [ui] multiple fixes related to split view and node status checks [PR](https://github.com/alicevision/Meshroom/pull/2568)
- [ui] Various minor UI fixes [PR](https://github.com/alicevision/Meshroom/pull/2563)
- [core] Node: Do not automatically upgrade unknown nodes in templates [PR](https://github.com/alicevision/Meshroom/pull/2558)
- [GraphEditor] Node: Check if unexposed `ListAttributes` contain links [PR](https://github.com/alicevision/Meshroom/pull/2578)
- [GraphEditor] Edge: Correctly update the `EdgeMouseArea` when moving nodes [PR](https://github.com/alicevision/Meshroom/pull/2613)
- Fix projects disappearing from the list of recent projects [PR](https://github.com/alicevision/Meshroom/pull/2615)
- [ImageGallery] Intrinsics table: Always fully instantiate the model before populating it [PR](https://github.com/alicevision/Meshroom/pull/2655)
- [ui] Graph: In minimal refresh, do not poll files for chunks run locally [PR](https://github.com/alicevision/Meshroom/pull/2672)
- Fix Meshroom App CLI `latest` option [PR](https://github.com/alicevision/Meshroom/pull/2675)
- [bin] `meshroom_batch`: Stop using removed `defaultCacheFolder` [PR](https://github.com/alicevision/Meshroom/pull/2715)
- [desc] Import `CREATE_NEW_PROCESS_GROUP` flag from `subprocess` [PR](https://github.com/alicevision/Meshroom/pull/2719)
- [ui] Reconstruction: Restore the `Slot` status of the `clear` method [PR](https://github.com/alicevision/Meshroom/pull/2732)
- [core] attribute: Fix `hasOutputConnections` for ListAttributes [PR](https://github.com/alicevision/Meshroom/pull/2731)
- Fix elapsed time when there is only one chunk [PR](https://github.com/alicevision/Meshroom/pull/2734)
- bugfix ExecMode status [PR](https://github.com/alicevision/Meshroom/pull/2737)
- [ui] Update node status when modified [PR](https://github.com/alicevision/Meshroom/pull/2738)
- [ui] [fix] MediaLibrary: Check if the model.source is actually an Attribute… [PR](https://github.com/alicevision/Meshroom/pull/2736)
- [ui] [fix] Viewer2D: Failure on MousePosition on some edge cases [PR](https://github.com/alicevision/Meshroom/pull/2741)
- [core] Templates test: Remove outdated `unregisterNodeType` import [PR](https://github.com/alicevision/Meshroom/pull/2750)
- [ui] GraphEditor fix: Remove useless link between height and implicitHeight [PR](https://github.com/alicevision/Meshroom/pull/2749)
- [core] Templates test: Access node descriptor from `NodePlugin` object [PR](https://github.com/alicevision/Meshroom/pull/2751)
- [core] Stop checking for templates in "pipelines" folder [PR](https://github.com/alicevision/Meshroom/pull/2752)
- [ui] [fix] Viewer2D: using the keyboard shortcuts (r,g,b,a) break the channelBox combobox [PR](https://github.com/alicevision/Meshroom/pull/2753)
- [ui] Reconstruction: Fix setup of temporary `CameraInit` nodes [PR](https://github.com/alicevision/Meshroom/pull/2762)
- [core] [fix] Fix camera see through not working when multiple cameraInit and image overlay dind't display anythind [PR](https://github.com/alicevision/Meshroom/pull/2761)
- [core] desc.node: Ensure all paths are sent to the command line as POSIX strings [PR](https://github.com/alicevision/Meshroom/pull/2760)
- [ui] Nodes: Update the deprecated import of QGraphicEffects. [PR](https://github.com/alicevision/Meshroom/pull/2755)
- [ui] Import images: Fix that trying to import images twic, the dialog… [PR](https://github.com/alicevision/Meshroom/pull/2763)
- Meshing: boundingBox working with qt6 [PR](https://github.com/alicevision/Meshroom/pull/2766)
- Fix manual frame selection in viewer 2D [PR](https://github.com/alicevision/Meshroom/pull/2769)
- [ui] app: Correctly evaluate env vars that enable/disable components [PR](https://github.com/alicevision/Meshroom/pull/2772)
- Fix for QFontDatabase crash on exit [PR](https://github.com/alicevision/Meshroom/pull/2776)
- [ui] Add project to recent projects when dropping a file [PR](https://github.com/alicevision/Meshroom/pull/2483)
- [ui] fix: Overlay image doesn't work on pipeline "Photogrametry experimental"  [PR](https://github.com/alicevision/Meshroom/pull/2780)
- [core] Parallelization: the cmdline suffix should be at the end [PR](https://github.com/alicevision/Meshroom/pull/2794)

### CI, Documentation and Build

- Add environment variable for the CI [PR](https://github.com/alicevision/Meshroom/pull/2492)
- Adding new tutorial [PR](https://github.com/alicevision/Meshroom/pull/2546)
- [ci] Use GitHub's workflows for the Windows CI instead of appveyor [PR](https://github.com/alicevision/Meshroom/pull/2551)
- [ci] Codecov: enable support for test run reports [PR](https://github.com/alicevision/Meshroom/pull/2659)
- change git clone link to use https link in "get the project" [PR](https://github.com/alicevision/Meshroom/pull/2700)
- [ci] Update Python version from 3.9.13 to 3.11 [PR](https://github.com/alicevision/Meshroom/pull/2758)
- [docker] Add Dockerfiles for Rocky 9 and handle Qt 6 installation [PR](https://github.com/alicevision/Meshroom/pull/2626)
- [doc] Update `INSTALL.md` and `README.md` files [PR](https://github.com/alicevision/Meshroom/pull/2787)
- [build] Fixes for the generation of Meshroom's executable [PR](https://github.com/alicevision/Meshroom/pull/2770)
- [doc] README.md: Add DeepWiki link, the AI documentation you can talk to [PR](https://github.com/alicevision/Meshroom/pull/2792)

### Contributors

[cbentejac](https://github.com/cbentejac), [demoulinv](https://github.com/demoulinv), [dependabot[bot]](https://github.com/apps/dependabot), [dyster](https://github.com/dyster), [elyasbny](https://github.com/elyasbny), [emmanuel-ferdman](https://github.com/emmanuel-ferdman), [fabiencastan](https://github.com/fabiencastan), [gregoire-dl](https://github.com/gregoire-dl), [jmelou](https://github.com/jmelou), [Just-Kiel](https://github.com/Just-Kiel), [mh0g](https://github.com/mh0g), [natowi](https://github.com/natowi), [nicolas-lambert-tc](https://github.com/nicolas-lambert-tc), [sbrood](https://github.com/sbrood), [servantftransperfect](https://github.com/servantftransperfect), [Sh1r0Yaksha](https://github.com/Sh1r0Yaksha), [waaake](https://github.com/waaake), [yann-lty](https://github.com/yann-lty)

## Meshroom 2023.3.0 (2023/12/07)

Based on [AliceVision 3.2.0](https://github.com/alicevision/AliceVision/tree/v3.2.0).

### Major Features

- New node for semantic image segmentation [PR](https://github.com/alicevision/Meshroom/pull/2076)
- Support pixel aspect ratio (no UI) [PR](https://github.com/alicevision/Meshroom/pull/2079)
- Noise reduction in HDR merging [PR](https://github.com/alicevision/Meshroom/pull/2072)

### Features

- [ui] 2D viewer: image sequence player [PR](https://github.com/alicevision/Meshroom/pull/1989)
- [bin] meshroom_batch: support multiple init nodes [PR](https://github.com/alicevision/Meshroom/pull/2137)
- [nodes] StructureFromMotion: Automatic alignment of the 3D reconstruction [PR](https://github.com/alicevision/Meshroom/pull/2199)
- New node for intrinsics and rig calibration using a multiview acquisition of a checkerboard [PR](https://github.com/alicevision/Meshroom/pull/2171)
- New Nodal Camera Tracking pipeline [PR](https://github.com/alicevision/Meshroom/pull/2200)
- Manage LCP in imageProcessing [PR](https://github.com/alicevision/Meshroom/pull/2042)
- [Viewer3D] Add slider to display cameras based on their resection IDs [PR](https://github.com/alicevision/Meshroom/pull/2235)

### Other Improvements

- Start Development 2023.3 [PR](https://github.com/alicevision/Meshroom/pull/2085)
- Node to split reconstructed and not reconstructed cameras [PR](https://github.com/alicevision/Meshroom/pull/1974)
- [core] Execute command line from node folder [PR](https://github.com/alicevision/Meshroom/pull/2093)
- [core] Add brackets option for GroupAttribute [PR](https://github.com/alicevision/Meshroom/pull/2094)
- Update Qt version to 5.15.2 [PR](https://github.com/alicevision/Meshroom/pull/1882)
- [pipelines] Panorama: Publish the panorama preview [PR](https://github.com/alicevision/Meshroom/pull/2106)
- [nodes] HDR Fusion: Correctly detect the number of brackets when there are several intrinsics [PR](https://github.com/alicevision/Meshroom/pull/2104)
- [nodes] ImageSegmentation: use ChoiceParam instead of ListAttribute for validClasses [PR](https://github.com/alicevision/Meshroom/pull/2109)
- [Panorama] Enforce priors after estimation [PR](https://github.com/alicevision/Meshroom/pull/1926)
- tolerant bracket size selection [PR](https://github.com/alicevision/Meshroom/pull/2113)
- [nodes] HDR Fusion: Do not send `nbBrackets` parameter to the command line when the bracket detection is automatic [PR](https://github.com/alicevision/Meshroom/pull/2117)
- [nodes] Remove limits on outliers for brackets detection [PR](https://github.com/alicevision/Meshroom/pull/2118)
- [nodes] LdrToHdrSampling: Exclude outliers from size computation [PR](https://github.com/alicevision/Meshroom/pull/2119)
- [nodes] HDR Fusion: Select group with largest bracket number in case of equality [PR](https://github.com/alicevision/Meshroom/pull/2121)
- [nodes] new exportLevels option in PanoramaPostProcessing [PR](https://github.com/alicevision/Meshroom/pull/2133)
- [ui] GraphEditor: Minor UI changes [PR](https://github.com/alicevision/Meshroom/pull/2125)
- [pipelines] publish downscaled panorama levels [PR](https://github.com/alicevision/Meshroom/pull/2147)
- [nodes] HDR Fusion: Use the same bracket detection as in AliceVision [PR](https://github.com/alicevision/Meshroom/pull/2154)
- AttributeEditor: Flag attributes with invalid values [PR](https://github.com/alicevision/Meshroom/pull/2141)
- [pipelines] Add colors for CameraTracking and Photog+CamTrack templates [PR](https://github.com/alicevision/Meshroom/pull/2114)
- [pipelines] add ImageSegmentation node to tracking pipelines [PR](https://github.com/alicevision/Meshroom/pull/2164)
- Camera exposure update [PR](https://github.com/alicevision/Meshroom/pull/2159)
- PanoramaInit: remove fake dependency [PR](https://github.com/alicevision/Meshroom/pull/2110)
- [nodes] Masking: Handle file extensions for masks and mask inversion for `ImageSegmentation` [PR](https://github.com/alicevision/Meshroom/pull/2165)
- [nodes] KeyframeSelection: Add `minBlockSize` param for multi-threading [PR](https://github.com/alicevision/Meshroom/pull/2161)
- [nodes] KeyframeSelection: Add support for masks [PR](https://github.com/alicevision/Meshroom/pull/2167)
- KeyframeSelection: Flag `outputExtension` attribute when it is set to "none" for video inputs [PR](https://github.com/alicevision/Meshroom/pull/2163)
- [blender] apply masks to scene preview [PR](https://github.com/alicevision/Meshroom/pull/2170)
- Add automatic method for HDR calibration [PR](https://github.com/alicevision/Meshroom/pull/2169)
- Multiple UI Improvements [PR](https://github.com/alicevision/Meshroom/pull/2173)
- [ui] FloatImageViewer: adapt resolution to zoom [PR](https://github.com/alicevision/Meshroom/pull/2148)
- [nodes] StructureFromMotion: Add new `logIntermediateSteps` parameter [PR](https://github.com/alicevision/Meshroom/pull/2182)
- sfm bootstraping [PR](https://github.com/alicevision/Meshroom/pull/2011)
- [nodes] PanoramaPostProcessing: Add attributes to change the outputs' names [PR](https://github.com/alicevision/Meshroom/pull/2193)
- [nodes] Meshing: expose minVis param [PR](https://github.com/alicevision/Meshroom/pull/2196)
- [ui] SequencePlayer: minor adjustments (fps, icon, play) [PR](https://github.com/alicevision/Meshroom/pull/2197)
- [pipelines] Rename Nodal Tracking to Nodal Camera Tracking [PR](https://github.com/alicevision/Meshroom/pull/2207)
- [nodes] DepthMap: increase size of blocks [PR](https://github.com/alicevision/Meshroom/pull/2203)
- [ui] ImageGallery: Add "Remove All Images" menu to clear all images [PR](https://github.com/alicevision/Meshroom/pull/2221)
- [bin] `meshroom_batch`: Add support for relative input and output paths [PR](https://github.com/alicevision/Meshroom/pull/2218)
- [pipelines] CamTrack: Add new template without calibration and update some parameters [PR](https://github.com/alicevision/Meshroom/pull/2216)
- Input color space setting [PR](https://github.com/alicevision/Meshroom/pull/2219)
- Use new SfmDataEntity plugin instead of AlembicEntity [PR](https://github.com/alicevision/Meshroom/pull/2208)
- [Viewer3D] Remove AlembicLoader file [PR](https://github.com/alicevision/Meshroom/pull/2228)
- [pipelines] CamTrack: Update default params for keyframes SfM [PR](https://github.com/alicevision/Meshroom/pull/2227)
- [pipelines] PhotogAndCamTrack: Disable automatic alignment in SfM [PR](https://github.com/alicevision/Meshroom/pull/2238)
- Automatic reorientation [PR](https://github.com/alicevision/Meshroom/pull/2236)
- Minor code clean-up and QML warning and error fixes [PR](https://github.com/alicevision/Meshroom/pull/2226)
- Add ancestor images info in view [PR](https://github.com/alicevision/Meshroom/pull/2242)
- [Viewer3D] Connect any change of the selected view ID to the SfmDataLoader [PR](https://github.com/alicevision/Meshroom/pull/2237)
- New utility nodes to create camera rigs and merge two sfmData [PR](https://github.com/alicevision/Meshroom/pull/2214)
- [pipelines] Add image segmentation to the Nodal Camera Tracking template [PR](https://github.com/alicevision/Meshroom/pull/2266)

### Bugfixes

- QML: Fix minor coercion error and warning [PR](https://github.com/alicevision/Meshroom/pull/2107)
- [ScenePreview] fix: 1st chunk was computing all views [PR](https://github.com/alicevision/Meshroom/pull/2108)
- [bin] meshroom_batch: Save the graph once it has been all set up and resolved [PR](https://github.com/alicevision/Meshroom/pull/2095)
- [nodes] HDR Fusion: Fix bracket detection [PR](https://github.com/alicevision/Meshroom/pull/2143)
- [core] Preserve edges by recreating all the nodes during UID evaluation [PR](https://github.com/alicevision/Meshroom/pull/2127)
- [bin] `meshroom_batch`: Fix input parsing for Windows [PR](https://github.com/alicevision/Meshroom/pull/2188)
- [nodes] ImageSegmentation: increase GPU requirements [PR](https://github.com/alicevision/Meshroom/pull/2195)
- [ui] ImageGallery: Disable "Visualize HDR" button after clearing images [PR](https://github.com/alicevision/Meshroom/pull/2180)
- [ui] Check for the existence of the `poses` key in SfM JSON files before accessing it [PR](https://github.com/alicevision/Meshroom/pull/2190)
- [nodes] CameraInit: fix tooltip focal is in mm [PR](https://github.com/alicevision/Meshroom/pull/2202)
- [ui] Viewer2D: various orientation fixes [PR](https://github.com/alicevision/Meshroom/pull/2212)
- [ui] ImageGallery: Use commands to set SfM attributes through the Image Gallery [PR](https://github.com/alicevision/Meshroom/pull/2220)
- [ui] Preserve last `CameraInit` index when updating the CameraInits list [PR](https://github.com/alicevision/Meshroom/pull/2145)
- [ui] Don't load a node's output in the 3DViewer if it has no 3D output [PR](https://github.com/alicevision/Meshroom/pull/2230)
- [pipelines] Photogrammetry Draft: Add a `PrepareDenseScene` node to the template [PR](https://github.com/alicevision/Meshroom/pull/2232)
- [Viewer3D] Bind the display status of the resection groups to QtAliceVision [PR](https://github.com/alicevision/Meshroom/pull/2257)
- [core] Only update the running chunk to `STOPPED` when stopping computations [PR](https://github.com/alicevision/Meshroom/pull/2258)

### CI, Build and Documentation

- Update build-ubuntu.sh [PR](https://github.com/alicevision/Meshroom/pull/1951)
- Set `ALICEVISION_SEMANTIC_SEGMENTATION_MODEL` variable during the initialisation [PR](https://github.com/alicevision/Meshroom/pull/2090)
- [build] Remove references to QmlAlembic in the build process [PR](https://github.com/alicevision/Meshroom/pull/2131)

### Contributors

[almarouk](https://github.com/almarouk), [cbentejac](https://github.com/cbentejac), [demoulinv](https://github.com/demoulinv), [fabiencastan](https://github.com/fabiencastan), [gregoire-dl](https://github.com/gregoire-dl), [mugulmd](https://github.com/mugulmd), [rakhnin](https://github.com/rakhnin), [servantftechnicolor](https://github.com/servantftechnicolor)


## Meshroom 2023.2.0 (2023/06/26)

Based on [AliceVision 3.1.0](https://github.com/alicevision/AliceVision/tree/v3.1.0).

### Major Features

- New Photometric Stereo nodes [PR](https://github.com/alicevision/Meshroom/pull/1853)
- [nodes] New CheckerboardDetection node [PR](https://github.com/alicevision/Meshroom/pull/1869)
- [nodes] Split360Images: support for SfMData file input and output [PR](https://github.com/alicevision/Meshroom/pull/1939)
- [sfmTransform] add auto mode [PR](https://github.com/alicevision/Meshroom/pull/1954)
- [nodes] DepthMap: New option for multi-resolution similarity estimation and optimizations [PR](https://github.com/alicevision/Meshroom/pull/1984)
- [nodes] Distortion calibration [PR](https://github.com/alicevision/Meshroom/pull/1986)
- Add a template for the HDR fusion [PR](https://github.com/alicevision/Meshroom/pull/2032)
- [pipelines] new CameraTracking pipeline [PR](https://github.com/alicevision/Meshroom/pull/2033)
- [pipelines] new photogrammetry and camera tracking pipeline [PR](https://github.com/alicevision/Meshroom/pull/2041)

### Features

- StructureFromMotion: Add new inputs parameters [PR](https://github.com/alicevision/Meshroom/pull/1980)
- [panorama] option to build contact sheet [PR](https://github.com/alicevision/Meshroom/pull/1945)
- Stitching color space [PR](https://github.com/alicevision/Meshroom/pull/1937)
- Add compression option for exr and jpg images [PR](https://github.com/alicevision/Meshroom/pull/1972)
- Add rec709 color space options [PR](https://github.com/alicevision/Meshroom/pull/1978)
- [nodes] rewrite RenderAnimatedCamera [PR](https://github.com/alicevision/Meshroom/pull/2030)
- [core] Detect and handle UID conflicts when loading a graph [PR](https://github.com/alicevision/Meshroom/pull/2059)

### Other Improvements

- Start Development Version 2023.2.0 [PR](https://github.com/alicevision/Meshroom/pull/1953)
- [core] Correctly parse status in version names when it exists [PR](https://github.com/alicevision/Meshroom/pull/1966)
- [tests] TemplatesVersion: Add message when compatibility assertion is raised [PR](https://github.com/alicevision/Meshroom/pull/1964)
- [ui] add new patterns to load images in viewer2D [PR](https://github.com/alicevision/Meshroom/pull/1975)
- [nodes] KeyframeSelection: Add support for SfMData files as inputs and outputs [PR](https://github.com/alicevision/Meshroom/pull/1967)
- [panorama] Panorama preview size [PR](https://github.com/alicevision/Meshroom/pull/1944)
- add trackbuilder node [PR](https://github.com/alicevision/Meshroom/pull/1987)
- [submitters] propagate REZ_PROD_PACKAGES_PATH environment variable [PR](https://github.com/alicevision/Meshroom/pull/1992)
- HDR images naming [PR](https://github.com/alicevision/Meshroom/pull/1999)
- [nodes] StructureFromMotion: new nbOutliersThreshold attribute [PR](https://github.com/alicevision/Meshroom/pull/2014)
- [ui] Reflect changes made in QtAliceVision refactorize PR [PR](https://github.com/alicevision/Meshroom/pull/1924)
- Exposure and format adjustment [PR](https://github.com/alicevision/Meshroom/pull/1983)
- [nodes] SfMTransform: add alignGround option [PR](https://github.com/alicevision/Meshroom/pull/2020)
- [nodes] ScenePreview: use base image name for naming output [PR](https://github.com/alicevision/Meshroom/pull/2035)
- [nodes] KeyframeSelection: Set a dynamic size for the node [PR](https://github.com/alicevision/Meshroom/pull/2039)
- KeyframeSelection: Add new parameter value to disable the export of keyframes [PR](https://github.com/alicevision/Meshroom/pull/2036)
- Viewer2D: Dynamically update the list of viewable outputs [PR](https://github.com/alicevision/Meshroom/pull/2044)
- [ui] ImageGallery: Display the name of the active `CameraInit` group [PR](https://github.com/alicevision/Meshroom/pull/2046)
- [nodes] StereoPhotometry: Fix some labels and descriptions [PR](https://github.com/alicevision/Meshroom/pull/2034)
- [ui] Display an icon on nodes that have viewable outputs [PR](https://github.com/alicevision/Meshroom/pull/2047)
- [ui] Display an icon on nodes that have viewable 3D outputs [PR](https://github.com/alicevision/Meshroom/pull/2052)
- [pipelines] cameraTracking: change StructureFromMotion parameters [PR](https://github.com/alicevision/Meshroom/pull/2055)
- [nodes] Harmonize and improve nodes descriptions  [PR](https://github.com/alicevision/Meshroom/pull/2063)
- [blender] preview: use cycles render engine [PR](https://github.com/alicevision/Meshroom/pull/2064)
- [blender] preview: occlusions in wireframe shading [PR](https://github.com/alicevision/Meshroom/pull/2071)

### Bugfixes, Build and Documentation

- [doc] RELEASING: Add example command to generate the release note [PR](https://github.com/alicevision/Meshroom/pull/1990)
- [core] Stats: Retrieve and set the GPU name if it is found [PR](https://github.com/alicevision/Meshroom/pull/1996)
- [bin] Fix all the scripts that had errors [PR](https://github.com/alicevision/Meshroom/pull/1995)
- [ui] ImageGallery: Reset viewpoints and intrinsics when removing all the images [PR](https://github.com/alicevision/Meshroom/pull/2031)
- [nodes] CameraInit: access intrinsic properties safely [PR](https://github.com/alicevision/Meshroom/pull/2040)
- [blender] preview: handle background image not found [PR](https://github.com/alicevision/Meshroom/pull/2045)
- Bump requests from 2.22.0 to 2.31.0 [PR](https://github.com/alicevision/Meshroom/pull/2018)
- [blender] preview: clear loaded images to avoid memory leak [PR](https://github.com/alicevision/Meshroom/pull/2053)
- Fix submit through simpleFarm [PR](https://github.com/alicevision/Meshroom/pull/2054)
- [ui] thumbnails: fallback if thumbnailDir could not be created [PR](https://github.com/alicevision/Meshroom/pull/2057)
- [core] fix transitive reduction when submitting graph [PR](https://github.com/alicevision/Meshroom/pull/2058)
- [doc] Update readme for custom pipelines and nodes [PR](https://github.com/alicevision/Meshroom/pull/2009)
- [core] Include the node's type in the UID computation [PR](https://github.com/alicevision/Meshroom/pull/2038)
- [doc] INSTALL: Add info about the sphere detection model [PR](https://github.com/alicevision/Meshroom/pull/2067)
- [blender] preview: use Freestyle for line art shading [PR](https://github.com/alicevision/Meshroom/pull/2074)
- Set `ALICEVISION_SPHERE_DETECTION_MODEL` variable during the initialisation [PR](https://github.com/alicevision/Meshroom/pull/2083)

### Contributors

[almarouk](https://github.com/almarouk), [cbentejac](https://github.com/cbentejac), [demoulinv](https://github.com/demoulinv), [earlywill](https://github.com/earlywill), [erikjwaxx](https://github.com/erikjwaxx), [fabiencastan](https://github.com/fabiencastan), [Garoli](https://github.com/Garoli), [gregoire-dl](https://github.com/gregoire-dl), [ICIbrahim](https://github.com/ICIbrahim), [jmelou](https://github.com/jmelou), [mugulmd](https://github.com/mugulmd), [serguei-k](https://github.com/serguei-k), [servantftechnicolor](https://github.com/servantftechnicolor), [simogasp](https://github.com/simogasp)


## Meshroom 2023.1.0 (2023/03/22)

Based on [AliceVision 3.0.0](https://github.com/alicevision/AliceVision/tree/v3.0.0).

### Release Notes Summary

- Major improvements of the depth map quality, performances and scalability. The full resolution can now be computed on most of the standard GPUs.
- FeatureExtraction is now using DSP-SIFT by default for the 3D Reconstruction pipeline.
- Capacity to create panoramas with very high resolutions using a limited amount of memory.
- Enhanced interpretation of RAW images, including new support for Adobe Digital Camera Profile and Lens Camera Profiles databases (if installed on your workstation).
- Improved color management with OCIO support and more options to export in various colorspaces including ACEScg.
- New graph templates enabling users to create custom pipelines.
- Expose a new experimental pipeline for Camera Tracking.
- Improved GraphEditor with copy-paste and multi-selection.
- Improved ImageGallery with thumbnails cache and search options.
- 2D Viewer is now using floating-point images by default.
- And a very large amount of UI improvements and bug fixes.

### Main Features

- [nodes] DepthMap: depth map improvements [PR](https://github.com/alicevision/Meshroom/pull/1818)
- Integration of AprilTag library according to issue #1179 and AliceVision pull request #950 [PR](https://github.com/alicevision/Meshroom/pull/1180)
- [nodes] add gps option to SfMTransform [PR](https://github.com/alicevision/Meshroom/pull/1477)
- [ui] add support for selecting multiple nodes at once [PR](https://github.com/alicevision/Meshroom/pull/1227)
- Image Gallery: Add a menu to set the StructureFromMotion initial pair from the gallery [PR](https://github.com/alicevision/Meshroom/pull/1936)
- Texturing Color Space [PR](https://github.com/alicevision/Meshroom/pull/1933)
- Add support for Lens Camera Profiles (LCP) [PR](https://github.com/alicevision/Meshroom/pull/1771)
- RAW advanced processing [PR](https://github.com/alicevision/Meshroom/pull/1918)
- Add new file watcher behaviours [PR](https://github.com/alicevision/Meshroom/pull/1812)
- Add internal attributes in "Notes" tab [PR](https://github.com/alicevision/Meshroom/pull/1744)
- New nodes for large memory use in panoramas [PR](https://github.com/alicevision/Meshroom/pull/1819)
- [ui] Thumbnail cache [PR](https://github.com/alicevision/Meshroom/pull/1861)
- [nodes] new SfMTriangulation node [PR](https://github.com/alicevision/Meshroom/pull/1842)
- Color management for RAW images [PR](https://github.com/alicevision/Meshroom/pull/1718)
- [ui] image gallery search bar [PR](https://github.com/alicevision/Meshroom/pull/1816)
- [ui] Viewer 2D: enable the HDR viewer by default [PR](https://github.com/alicevision/Meshroom/pull/1793)
- [ui] Improve the manipulator of the panorama viewer [PR](https://github.com/alicevision/Meshroom/pull/1707)
- Color space management [PR](https://github.com/alicevision/Meshroom/pull/1792)
- Show generated images in 2D viewer when double-clicking on node [PR](https://github.com/alicevision/Meshroom/pull/1776)
- [ui] Elapsed time indicators in log [PR](https://github.com/alicevision/Meshroom/pull/1787)
- [nodes] SfMTransform: add auto_from_cameras_x_axis [PR](https://github.com/alicevision/Meshroom/pull/1390)
- Graph Editor: Support copy/paste of selected nodes and scene import [PR](https://github.com/alicevision/Meshroom/pull/1758)
- [Feature Matching] Add an option to remove matches without enough motion [PR](https://github.com/alicevision/Meshroom/pull/1740)
- Output in ACES or ACEScg color space [PR](https://github.com/alicevision/Meshroom/pull/1681)
- Use project files to define pipelines [PR](https://github.com/alicevision/Meshroom/pull/1727)
- [nodes] StructureFromMotion: Add option computeStructureColor [PR](https://github.com/alicevision/Meshroom/pull/1635)
- [core] add env var to load nodes from multiple folders [PR](https://github.com/alicevision/Meshroom/pull/1616)
- Depth map refactoring [PR](https://github.com/alicevision/Meshroom/pull/680)
- Draft Reconstruction pipeline [PR](https://github.com/alicevision/Meshroom/pull/1489)
- [ui] Add filters to image gallery [PR](https://github.com/alicevision/Meshroom/pull/1500)
- [nodes] New node "RenderAnimatedCamera" using blender API [PR](https://github.com/alicevision/Meshroom/pull/1432)
- New node to import known poses for various file formats [PR](https://github.com/alicevision/Meshroom/pull/1475)
- New ImageMasking and MeshMasking nodes [PR](https://github.com/alicevision/Meshroom/pull/1483)
- Create Split360Images Node [PR](https://github.com/alicevision/Meshroom/pull/1464)
- New lens distortion calibration node [PR](https://github.com/alicevision/Meshroom/pull/1403)
- New experimental camera tracking pipeline [PR](https://github.com/alicevision/Meshroom/pull/1379)
- [multiview] New pipeline "Photogrammetry and Camera Tracking" [PR](https://github.com/alicevision/Meshroom/pull/1429)
- [nodes] KeyframeSelection: Rework the node and add parameters for new selection methods [PR](https://github.com/alicevision/Meshroom/pull/1880)


### Other Improvements

- [nodes] ImageProcessing: Add and hide the fringing correction in the LCP [PR](https://github.com/alicevision/Meshroom/pull/1930)
- Update highlight mode description in imageProcessing node [PR](https://github.com/alicevision/Meshroom/pull/1928)
- [ui] Prompt a warning dialog when attempting to submit an unsaved project [PR](https://github.com/alicevision/Meshroom/pull/1927)
- [panorama] force pyramid levels count in compositing [PR](https://github.com/alicevision/Meshroom/pull/1919)
- [ui] Add a new advanced menu action to load templates like regular projects [PR](https://github.com/alicevision/Meshroom/pull/1920)
- [panorama] New option to disable compositing tiling [PR](https://github.com/alicevision/Meshroom/pull/1916)
- [sfmtransform] Transformation parameter availability [PR](https://github.com/alicevision/Meshroom/pull/1876)
- Apply DCP metadata in imageProcessing [PR](https://github.com/alicevision/Meshroom/pull/1879)
- [ui] FeaturesViewer: track endpoints [PR](https://github.com/alicevision/Meshroom/pull/1838)
- LdrToHdrMerge node: Add a checkbox enabling the manual setting of the reference bracket for HDR merging [PR](https://github.com/alicevision/Meshroom/pull/1849)
- [ui] Display nodes computed in another Meshroom instance as "Computed Externally" [PR](https://github.com/alicevision/Meshroom/pull/1862)
- [ui] Use the location of the most recently imported images as the base folder for the "Import Images" dialog [PR](https://github.com/alicevision/Meshroom/pull/1864)
- [ui] GraphEditor: use maxZoom to fit on nodes [PR](https://github.com/alicevision/Meshroom/pull/1865)
- [ui] Viewer2D: support all Exif orientation tags [PR](https://github.com/alicevision/Meshroom/pull/1857)
- Use DCP by default if the database is set and create errors on missing DCP files [PR](https://github.com/alicevision/Meshroom/pull/1863)
- [ui] Load 3D Depth Map: minor improvements [PR](https://github.com/alicevision/Meshroom/pull/1852)
- [ui] Checkbox to enable/disable 8-bit viewer [PR](https://github.com/alicevision/Meshroom/pull/1858)
- Add Ripple submitter [PR](https://github.com/alicevision/Meshroom/pull/1844)
- [ui] ImageGallery: Increase the GridView's cache capacity [PR](https://github.com/alicevision/Meshroom/pull/1855)
- [ui] Reorganize the "File" menu [PR](https://github.com/alicevision/Meshroom/pull/1856)
- [nodes] rename: remove "utils" from executables names [PR](https://github.com/alicevision/Meshroom/pull/1848)
- [ui] Integrate QtOIIO into QtAliceVision [PR](https://github.com/alicevision/Meshroom/pull/1831)
- Add nl means denoising open cv in image processing node [PR](https://github.com/alicevision/Meshroom/pull/1719)
- [core] Add cgroups support to meshroom [PR](https://github.com/alicevision/Meshroom/pull/1836)
- Remove support for Python 2 [PR](https://github.com/alicevision/Meshroom/pull/1837)
- [submitters] Add an option to update the job title on submitters [PR](https://github.com/alicevision/Meshroom/pull/1824)
- [ui] GraphEditor: create new pipelines with the node menu [PR](https://github.com/alicevision/Meshroom/pull/1833)
- [bin] meshroom_batch: allow passing list of values to param overrides [PR](https://github.com/alicevision/Meshroom/pull/1811)
- [ui] ImageGallery: update the Viewer2D correctly when the GridView's current item changes [PR](https://github.com/alicevision/Meshroom/pull/1823)
- [ui] keyboard shortcut: press tab to open node menu [PR](https://github.com/alicevision/Meshroom/pull/1813)
- Update bounding box display to use the correct geometric frame [PR](https://github.com/alicevision/Meshroom/pull/1805)
- [ui] Paste nodes at the center of the Graph Editor when it does not contain the mouse [PR](https://github.com/alicevision/Meshroom/pull/1788)
- Use most recent project as base folder for file dialogs [PR](https://github.com/alicevision/Meshroom/pull/1778)
- [ui] Restrain the "copy/paste nodes" shortcuts to the GraphEditor [PR](https://github.com/alicevision/Meshroom/pull/1782)
- [core] Set the "template" flag to "false" when saving a project as a regular file [PR](https://github.com/alicevision/Meshroom/pull/1777)
- [ui] Display computation time for "running" or "finished" nodes [PR](https://github.com/alicevision/Meshroom/pull/1764)
- Removed duplicated call to findnodes [PR](https://github.com/alicevision/Meshroom/pull/1767)
- Add dedicated "minimal" mode for templates [PR](https://github.com/alicevision/Meshroom/pull/1754)
- [ui] Reduce confusion when qml loading fails [PR](https://github.com/alicevision/Meshroom/pull/1728)
- [ui] Update intrinsics table when switching between groups [PR](https://github.com/alicevision/Meshroom/pull/1755)
- [bin] batch: allow to set params inside groups [PR](https://github.com/alicevision/Meshroom/pull/1665)
- [camerainit] update parameters to use focal in mm [PR](https://github.com/alicevision/Meshroom/pull/1652)
- [bin] newNodeType: update [PR](https://github.com/alicevision/Meshroom/pull/1630)
- [minor] renderfarm submission with rez [PR](https://github.com/alicevision/Meshroom/pull/1629)
- [ui] widgets visibility options [PR](https://github.com/alicevision/Meshroom/pull/1545)
- [bin] Avoid multi-threading in non-interactive computation [PR](https://github.com/alicevision/Meshroom/pull/1553)
- [nodes] Mesh*: use file extension to choose the file format [PR](https://github.com/alicevision/Meshroom/pull/1524)
- Upgrade Texturing node and add multiples mesh file types [PR](https://github.com/alicevision/Meshroom/pull/1508)
- Optical center relative to the image center [PR](https://github.com/alicevision/Meshroom/pull/1509)
- [core] Improve project files upgrade [PR](https://github.com/alicevision/Meshroom/pull/1503)
- [ui] Add a clear images button  [PR](https://github.com/alicevision/Meshroom/pull/1467)
- [ui] highlight the edge that will be deleted [PR](https://github.com/alicevision/Meshroom/pull/1434)
- Update 2d viewer for new Track drawing mode of QtAliceVision  [PR](https://github.com/alicevision/Meshroom/pull/1435)
- Add cli script to start Meshroom on Windows [PR](https://github.com/alicevision/Meshroom/pull/1169)
- Allow replacing edges [PR](https://github.com/alicevision/Meshroom/pull/1355)
- No cmd line range arguments if we have only a single chunk [PR](https://github.com/alicevision/Meshroom/pull/1426)
- [nodes] ExportAnimatedCameras: new sfmDataFilter parameter [PR](https://github.com/alicevision/Meshroom/pull/1428)
- Node highlight radius [PR](https://github.com/alicevision/Meshroom/pull/1357)

### Bug Fixes, Build and Documentation

- [ui] Fix conditions on which the prompt asking the user to save a project before submitting it to the render farm relies [PR](https://github.com/alicevision/Meshroom/pull/1942)
- [ui] ImageGallery: Allow image drop if the active group is not computing [PR](https://github.com/alicevision/Meshroom/pull/1941)
- [ui] Viewer2D: fix displayed metadata [PR](https://github.com/alicevision/Meshroom/pull/1915)
- [setup] add all scripts in bin/ as executables [PR](https://github.com/alicevision/Meshroom/pull/1419)
- Add a unit test to check the node versions of templates [PR](https://github.com/alicevision/Meshroom/pull/1799)
- [nodes] Split360Images: update attributes to software version 2.0 [PR](https://github.com/alicevision/Meshroom/pull/1935)
- [ci] upgrade github actions rules [PR](https://github.com/alicevision/Meshroom/pull/1834)
- Update INSTALL.md [PR](https://github.com/alicevision/Meshroom/pull/1803)
- [docs] Python documentation generation using Sphinx [PR](https://github.com/alicevision/Meshroom/pull/1794)
- Documentation update : how to use Meshroom without building AliceVision [PR](https://github.com/alicevision/Meshroom/pull/1487)
- [pipelines] Panorama: Fix inputs of the "Publish" nodes [PR](https://github.com/alicevision/Meshroom/pull/1922)
- [nodes] ExportAnimatedCameras: fix output params labels [PR](https://github.com/alicevision/Meshroom/pull/1911)
- [nodes] PanoramaWarping: remove obsolete image output attributes [PR](https://github.com/alicevision/Meshroom/pull/1914)
- Fix the documentation related to Panorama nodes [PR](https://github.com/alicevision/Meshroom/pull/1917)
- Fix missing Publish nodes in templates [PR](https://github.com/alicevision/Meshroom/pull/1903)
- [ui] Intrinsics: Fix warnings and exceptions [PR](https://github.com/alicevision/Meshroom/pull/1898)
- [ui] fix thumbnail cache bugs [PR](https://github.com/alicevision/Meshroom/pull/1893)
- [ImageGallery] Match the filter selection with the gallery's display [PR](https://github.com/alicevision/Meshroom/pull/1899)
- [ui] fix "Sync Camera with Image Selection" [PR](https://github.com/alicevision/Meshroom/pull/1888)
- Fix exceptions raised when accessing attributes that either do not exist or are not associated to a graph [PR](https://github.com/alicevision/Meshroom/pull/1889)
- fix(sec): upgrade psutil to 5.6.7 [PR](https://github.com/alicevision/Meshroom/pull/1843)
- [ui] Fix all "TypeError" QML warnings [PR](https://github.com/alicevision/Meshroom/pull/1839)
- [ui] Viewer2D: fix minor issues [PR](https://github.com/alicevision/Meshroom/pull/1829)
- Fix crash when importing images with non-ascii characters in their filepath [PR](https://github.com/alicevision/Meshroom/pull/1809)
- Fix and prevent mismatches between an attribute's type and its default value's type [PR](https://github.com/alicevision/Meshroom/pull/1784)
- Fix various typos [PR](https://github.com/alicevision/Meshroom/pull/1768)
- [ui] ImageGallery: fix some minor issues [PR](https://github.com/alicevision/Meshroom/pull/1766)
- [core] fix logging of nodes loading [PR](https://github.com/alicevision/Meshroom/pull/1748)
- Fix node duplication/removal behaviour [PR](https://github.com/alicevision/Meshroom/pull/1738)
- [ui] Fix offset between the mouse's position and the tip of the edge when connecting two nodes [PR](https://github.com/alicevision/Meshroom/pull/1732)
- Fix compatibility with Python 3 [PR](https://github.com/alicevision/Meshroom/pull/1734)
- Fix stats [PR](https://github.com/alicevision/Meshroom/pull/1704)
- [ui] ImageGallery: fix missing function changeCurrentIndex [PR](https://github.com/alicevision/Meshroom/pull/1679)
- [UI] StatViewer: fix displayed unit [PR](https://github.com/alicevision/Meshroom/pull/1547)
- [ui] fix uvCenterOffset [PR](https://github.com/alicevision/Meshroom/pull/1551)
- Fix meshroom_batch [PR](https://github.com/alicevision/Meshroom/pull/1521)
- Fix incompatibility with recent cx_Freeze [PR](https://github.com/alicevision/Meshroom/pull/1480)
- [bin] meshroom_batch: fix typo in pipeline names [PR](https://github.com/alicevision/Meshroom/pull/1377)
- Removing `io_counters` from the ProcStatatistics [PR](https://github.com/alicevision/Meshroom/pull/1374)
- Fix NameError [PR](https://github.com/alicevision/Meshroom/pull/1312)
- [ui] Image Gallery: Fix the display of the intrinsics table with temporary CameraInit nodes [PR](https://github.com/alicevision/Meshroom/pull/1934)
- [ui] Correctly update the Viewer 2D when there are temporary CameraInit nodes [PR](https://github.com/alicevision/Meshroom/pull/1931)
- [ui] Clear Images: Request a graph update after resetting the viewpoints and intrinsics [PR](https://github.com/alicevision/Meshroom/pull/1929)
- [ui] Improve "Clear Images" action's behaviour and performance [PR](https://github.com/alicevision/Meshroom/pull/1897)
- [Viewer] Load and unload the SfMStats components explicitly every time they are shown and hidden  [PR](https://github.com/alicevision/Meshroom/pull/1912)
- [ui] Drag&Drop: Use a pool of threads for asynchronous intrinsics computations [PR](https://github.com/alicevision/Meshroom/pull/1896)
- [nodes] CameraInit: upgrade version following the parameters changes [PR](https://github.com/alicevision/Meshroom/pull/1874)
- [ui] app: temporary workaround for qInstallMessageHandler [PR](https://github.com/alicevision/Meshroom/pull/1873)
- [ui] ImageGallery: fix the DB path in the "Edit Sensor Database" dialog [PR](https://github.com/alicevision/Meshroom/pull/1860)
- [ui] Correctly determine if a graph is being computed locally and update nodes' statuses accordingly [PR](https://github.com/alicevision/Meshroom/pull/1832)
- [nodes] CameraInit: all intrinsics parameters should invalidate [PR](https://github.com/alicevision/Meshroom/pull/1747)
- [ci] add bug to the list of tag to skip the stale check [PR](https://github.com/alicevision/Meshroom/pull/1745)
- Fix various typos in the source code [PR](https://github.com/alicevision/Meshroom/pull/1606)
- Update ion startup [PR](https://github.com/alicevision/Meshroom/pull/1815)
- New script to launch meshroom under ion environment [PR](https://github.com/alicevision/Meshroom/pull/1783)
- [doc] fix the bibtex [PR](https://github.com/alicevision/Meshroom/pull/1537)
- [doc] readme: add citation [PR](https://github.com/alicevision/Meshroom/pull/1520)

### Contributors

Thanks to [Fabien Servant](https://github.com/servantftechnicolor), [Gregoire De Lillo](https://github.com/gregoire-dl), [Vincent Demoulin](https://github.com/demoulinv), [Thomas Zorroche](https://github.com/Thomas-Zorroche), [Povilas Kanapickas](https://github.com/p12tic), [Simone Gasparini](https://github.com/simogasp), [Candice Bentejac](https://github.com/cbentejac), [Loic Vital](https://github.com/mugulmd), [Charles Johnson](https://github.com/ChemicalXandco), [Jean Melou](https://github.com/jmelou), [Matthieu Hog](https://github.com/mh0g), [Simon Schuette](https://github.com/natowi), [Ludwig Chieng](https://github.com/ludchieng), [Vincent Scavinner](https://github.com/vscav), [Nils Landrodie](https://github.com/N0Ls), [Stella Tan](https://github.com/tanstella) for the major contributions.

Other release contributors:
[asoftbird](https://github.com/asoftbird), [DanielDelaporus](https://github.com/DanielDelaporus), [DataBeaver](https://github.com/DataBeaver), [elektrokokke](https://github.com/elektrokokke), [fabiencastan](https://github.com/fabiencastan), [Garoli](https://github.com/Garoli), [ghost](https://github.com/ghost), [hammady](https://github.com/hammady), [luzpaz](https://github.com/luzpaz), [MakersF](https://github.com/MakersF), [pen4](https://github.com/pen4), [remmel](https://github.com/remmel), [wolfgangp](https://github.com/wolfgangp)



## Release 2021.1.0 (2021/02/26)

Based on [AliceVision 2.4.0](https://github.com/alicevision/AliceVision/tree/v2.4.0).

### Release Notes Summary

 - [panorama] PanoramaCompositing: new algorithm with tiles to deal with large panoramas [PR](https://github.com/alicevision/meshroom/pull/1173)
 - [feature] Improve robustness of sift features extraction on challenging images: update default values, add new filtering and add dsp-sift variation [PR](https://github.com/alicevision/meshroom/pull/1164)
 - [ui] Improve Graph Editor UX with better visualization of nodes connections, the ability to accumulate nodes to compute locally or the ability to compute multiple branches in parallel on renderfarm with a new locking system per node, etc. [PR](https://github.com/alicevision/meshroom/pull/612)
 - [nodes] Meshing: improve mesh quality with a new post-processing. Cells empty/full status are filtered by solid angle ratio to favor smoothness. [PR](https://github.com/alicevision/meshroom/pull/1274)
 - [nodes] MeshFiltering: smoothing & filtering on subset of the geometry [PR](https://github.com/alicevision/meshroom/pull/1272)
 - [ui] Viewer: fix gain/gamma behavior and use non-linear sliders [PR](https://github.com/alicevision/meshroom/pull/1092)

### Other Improvements and Bug Fixes

 - [core] taskManager: downgrade status per chunk [PR](https://github.com/alicevision/meshroom/pull/1210)
 - [core] Improve graph dependencies: dependencies to an input parameter is not a real dependency [PR](https://github.com/alicevision/meshroom/pull/1182)
 - [nodes] Meshing: Add `addMaskHelperPoints` option [PR](https://github.com/alicevision/meshroom/pull/1273)
 - [nodes] Meshing: More control on graph cut post processing [PR](https://github.com/alicevision/meshroom/pull/1284)
 - [nodes] Meshing: new cells filtering by solid angle ratio [PR](https://github.com/alicevision/meshroom/pull/1274)
 - [nodes] Meshing: add seed and voteFilteringForWeaklySupportedSurfaces [PR](https://github.com/alicevision/meshroom/pull/1268)
 - [nodes] Add some mesh utilities nodes [PR](https://github.com/alicevision/meshroom/pull/1271)
 - [nodes] SfmTransform: new from_center_camera [PR](https://github.com/alicevision/meshroom/pull/1281)
 - [nodes] Panorama: new options to init with known poses [PR](https://github.com/alicevision/meshroom/pull/1230)
 - [nodes] FeatureMatching: add cross verification [PR](https://github.com/alicevision/meshroom/pull/1276)
 - [nodes] ExportAnimatedCamera: New option to export undistort maps in EXR format [PR](https://github.com/alicevision/meshroom/pull/1229)
 - [nodes] new wip node `LightingEstimation` to estimate spherical harmonics from normal map and albedo [PR](https://github.com/alicevision/meshroom/pull/390)
 - [nodes] CameraInit: add a boolean for white balance use [PR](https://github.com/alicevision/meshroom/pull/1162)
 - [ui] fix error on live reconstruction [PR](https://github.com/alicevision/meshroom/pull/1145)
 - [ui] init saveAs folder [PR](https://github.com/alicevision/meshroom/pull/1099)
 - [ui] add link to online documentation in 'Help' menu [PR](https://github.com/alicevision/meshroom/pull/1279)
 - [ui] New node menu categories [PR](https://github.com/alicevision/meshroom/pull/1278)


## Release 2020.1.1 (2020/10/14)

Based on [AliceVision 2.3.1](https://github.com/alicevision/AliceVision/tree/v2.3.1).

 - [core] Fix crashes on process statistics (windows-only) [PR](https://github.com/alicevision/meshroom/pull/1096)


## Release 2020.1.0 (2020/10/09)

Based on [AliceVision 2.3.0](https://github.com/alicevision/AliceVision/tree/v2.3.0).

### Release Notes Summary

 - [nodes] New Panorama Stitching nodes with support for fisheye lenses [PR](https://github.com/alicevision/meshroom/pull/639) [PR](https://github.com/alicevision/meshroom/pull/808)
 - [nodes] HDR: Largely improved HDR calibration, including new LdrToHdrSampling for optimal sample selection [PR](https://github.com/alicevision/meshroom/pull/808) [PR](https://github.com/alicevision/meshroom/pull/1016) [PR](https://github.com/alicevision/meshroom/pull/990)
 - [ui] Viewer3D: Input bounding box (Meshing) & manual transformation (SfMTransform) thanks to a new 3D Gizmo [PR](https://github.com/alicevision/meshroom/pull/978)
 - [ui] Sync 3D camera with image selection [PR](https://github.com/alicevision/meshroom/pull/633) 
 - [ui] New HDR (floating point) Image Viewer [PR](https://github.com/alicevision/meshroom/pull/795)
 - [ui] Ability to load depth maps into 2D and 3D Viewers [PR](https://github.com/alicevision/meshroom/pull/769) [PR](https://github.com/alicevision/meshroom/pull/657) 
 - [ui] New features overlay in Viewer2D allows to display tracks and landmarks [PR](https://github.com/alicevision/meshroom/pull/873) [PR](https://github.com/alicevision/meshroom/pull/1001)
 - [ui] Add SfM statistics [PR](https://github.com/alicevision/meshroom/pull/873)
 - [ui] Visual interface for node resources usage [PR](https://github.com/alicevision/meshroom/pull/564)
 - [nodes] Coordinate system alignment to specific markers or between scenes [PR](https://github.com/alicevision/meshroom/pull/652)
 - [nodes] New Sketchfab upload node [PR](https://github.com/alicevision/meshroom/pull/712)
 - [ui] Dynamic Parameters: add a new 'enabled' property to node's attributes [PR](https://github.com/alicevision/meshroom/pull/1007) [PR](https://github.com/alicevision/meshroom/pull/1027)
 - [ui] Viewer: add Camera Response Function display [PR](https://github.com/alicevision/meshroom/pull/1020) [PR](https://github.com/alicevision/meshroom/pull/1041)
 - [ui] UI improvements in the Viewer2D and ImageGallery [PR](https://github.com/alicevision/meshroom/pull/823)
 - [bin] Improve Meshroom command line [PR](https://github.com/alicevision/meshroom/pull/759) [PR](https://github.com/alicevision/meshroom/pull/632)
 - [nodes] New ImageProcessing node [PR](https://github.com/alicevision/meshroom/pull/839) [PR](https://github.com/alicevision/meshroom/pull/970) [PR](https://github.com/alicevision/meshroom/pull/941)
 - [nodes] `FeatureMatching` Add `fundamental_with_distortion` option [PR](https://github.com/alicevision/meshroom/pull/931)
 - [multiview] Declare more recognized image file extensions [PR](https://github.com/alicevision/meshroom/pull/965)
 - [multiview] More generic metadata support [PR](https://github.com/alicevision/meshroom/pull/957)

### Other Improvements and Bug Fixes

 - [nodes] CameraInit: New viewId generation and selection of allowed intrinsics [PR](https://github.com/alicevision/meshroom/pull/973)
 - [core] Avoid error during project load on border cases [PR](https://github.com/alicevision/meshroom/pull/991)
 - [core] Compatibility : Improve list of groups update [PR](https://github.com/alicevision/meshroom/pull/791)
 - [core] Invalidation hooks [PR](https://github.com/alicevision/meshroom/pull/732)
 - [core] Log manager for Python based nodes [PR](https://github.com/alicevision/meshroom/pull/631)
 - [core] new Node Update Hooks mechanism [PR](https://github.com/alicevision/meshroom/pull/733)
 - [core] Option to make chunks optional [PR](https://github.com/alicevision/meshroom/pull/778)
 - [nodes] Add methods in ImageMatching and features in StructureFromMotion and FeatureMatching [PR](https://github.com/alicevision/meshroom/pull/768)
 - [nodes] FeatureExtraction: add maxThreads argument [PR](https://github.com/alicevision/meshroom/pull/647) 
 - [nodes] Fix python nodes being blocked by log [PR](https://github.com/alicevision/meshroom/pull/783)
 - [nodes] ImageProcessing: add new option to fix non finite pixels [PR](https://github.com/alicevision/meshroom/pull/1057)
 - [nodes] Meshing: simplify input depth map folders [PR](https://github.com/alicevision/meshroom/pull/951)
 - [nodes] PanoramaCompositing: add a new graphcut option to improve seams [PR](https://github.com/alicevision/meshroom/pull/1026)
 - [nodes] PanoramaCompositing: option to select the percentage of upscaled pixels [PR](https://github.com/alicevision/meshroom/pull/1049)
 - [nodes] PanoramaInit: add debug circle detection option [PR](https://github.com/alicevision/meshroom/pull/1069)
 - [nodes] PanoramaInit: New parameter to set an extra image rotation to each camera declared the input xml [PR](https://github.com/alicevision/meshroom/pull/1046)
 - [nodes] SfmTransfer: New option to transfer intrinsics parameters [PR](https://github.com/alicevision/meshroom/pull/1053)
 - [nodes] StructureFromMotion: Add features’s scale as an option [PR](https://github.com/alicevision/meshroom/pull/822) [PR](https://github.com/alicevision/meshroom/pull/817)
 - [nodes] Texturing: add options for retopoMesh & reorganise options [PR](https://github.com/alicevision/meshroom/pull/571)
 - [nodes] Texturing: put downscale to 2 by default [PR](https://github.com/alicevision/meshroom/pull/1048)
 - [sfm] Add option to include 'unknown' feature types in ConvertSfMFormat, needed to be used on dense point cloud from the Meshing node [PR](https://github.com/alicevision/meshroom/pull/584)
 - [ui] Automatically update layout when needed [PR](https://github.com/alicevision/meshroom/pull/989)
 - [ui] Avoid crash in 3D with large panoramas [PR](https://github.com/alicevision/meshroom/pull/1061)
 - [ui] Fix graph axes naming for ram statistics [PR](https://github.com/alicevision/meshroom/pull/1033)
 - [ui] NodeEditor: minor improvements with single tab group and status table [PR](https://github.com/alicevision/meshroom/pull/637)
 - [ui] Viewer3D: Display equirectangular images as environment maps [PR](https://github.com/alicevision/meshroom/pull/731) 
 - [windows] Fix open recent broken on windows and remove unnecessary warnings [PR](https://github.com/alicevision/meshroom/pull/940)

### Build, CI, Documentation

 - [build] Fix cxFreeze version for Python 2.7 compatibility [PR](https://github.com/alicevision/meshroom/pull/634)
 - [ci] Add github Actions [PR](https://github.com/alicevision/meshroom/pull/1051)
 - [ci] AppVeyor: Update build environment and save artifacts [PR](https://github.com/alicevision/meshroom/pull/875)
 - [ci] Travis: Update environment, remove Python 2.7 & add 3.8 [PR](https://github.com/alicevision/meshroom/pull/874)
 - [docker] Clean Dockerfiles [PR](https://github.com/alicevision/meshroom/pull/1054)
 - [docker] Move to PySide2 / Qt 5.14.1
 - [docker] Fix some packaging issues of the release 2019.2.0 [PR](https://github.com/alicevision/meshroom/pull/627)
 - [github] Add exemptLabels [PR](https://github.com/alicevision/meshroom/pull/801)
 - [github] Add issue templates [PR](https://github.com/alicevision/meshroom/pull/579)
 - [github] Add template for questions / help only  [PR](https://github.com/alicevision/meshroom/pull/629)
 - [github] Added automatic stale detection and closing for issues [PR](https://github.com/alicevision/meshroom/pull/598)
 - [python] Import ABC from collections.abc [PR](https://github.com/alicevision/meshroom/pull/983)

For more details see all PR merged: https://github.com/alicevision/meshroom/milestone/10

See [AliceVision 2.3.0 Release Notes](https://github.com/alicevision/AliceVision/blob/v2.3.0/CHANGES.md) for more details about algorithmic changes.


## Release 2019.2.0 (2019/08/08)

Based on [AliceVision 2.2.0](https://github.com/alicevision/AliceVision/tree/v2.2.0).

Release Notes Summary:

 - Visualisation: New visualization module of the features extraction. [PR](https://github.com/alicevision/meshroom/pull/539), [New QtAliceVision](https://github.com/alicevision/QtAliceVision)
 - Support for RAW image files.
 - Texturing: Largely improve the Texturing quality.
 - Texturing: Speed improvements.
 - Texturing: Add support for UDIM.
 - Meshing: Export the dense point cloud in Alembic.
 - Meshing: New option to export the full raw dense point cloud (with all 3D points candidates before cut and filtering).
 - Meshing: Adds an option to export color data per vertex and MeshFiltering correctly preserves colors.

Full Release Notes:

 - Move to PySide2 / Qt 5.13
 - SfMDataIO: Change root nodes (XForms instead of untyped objects) of Alembic SfMData for better interoperability with other 3D graphics applications (in particular Blender and Houdini).
 - Improve performance of log display and node status update. [PR](https://github.com/alicevision/meshroom/pull/466) [PR](https://github.com/alicevision/meshroom/pull/548)
 - Viewer3D: Add support for vertex-colored meshes. [PR](https://github.com/alicevision/meshroom/pull/550)
 - New pipeline input for meshroom_photogrammetry command line and minor fixes to the input arguments. [PR](https://github.com/alicevision/meshroom/pull/567) [PR](https://github.com/alicevision/meshroom/pull/577)
 - New arguments to meshroom. [PR](https://github.com/alicevision/meshroom/pull/413)
 - HDR: New HDR module for the fusion of multiple LDR images.
 - PrepareDenseScene: Add experimental option to correct Exposure Values (EV) of input images to uniformize dataset exposures.
 - FeatureExtraction: Include CCTag in the release binaries both on Linux and Windows.
 - ConvertSfMFormat: Enable to use simple regular expressions in the image white list of the ConvertSfMFormat. This enables to filter out cameras based on their filename.

For more details see all PR merged: https://github.com/alicevision/meshroom/milestone/9
See [AliceVision 2.2.0 Release Notes](https://github.com/alicevision/AliceVision/blob/v2.2.0/CHANGES.md)
for more details about algorithmic changes.


## Release 2019.1.0 (2019/02/27)

Based on [AliceVision 2.1.0](https://github.com/alicevision/AliceVision/tree/v2.1.0).

Release Notes Summary:
 - 3D Viewer: Load and compare multiple assets with cache mechanism and improved navigation
 - Display camera intrinsic information extracted from metadata analysis
 - Easier access to a more complete sensor database with a more reliable camera model matching algorithm.
 - Attribute Editor: Hide advanced/experimental parameters by default to improve readability and simplify access to the most useful, high-level settings.  Advanced users can still enable them to have full access to internal thresholds.
 - Graph Editor: Improved set of contextual tools with `duplicate`/`remove`/`delete data` actions with `From Here` option.
 - Nodes: Homogenization of inputs / outputs parameters
 - Meshing: Better, faster and configurable estimation of the space to reconstruct based on the sparse point cloud (new option `estimateSpaceFromSfM`). Favors high-density areas and helps removing badly defined ones.
 - Draft Meshing (no CUDA required): the result of the sparse reconstruction can now be directly meshed to get a 3D model preview without computing the depth maps.
 - MeshFiltering: Now keeps all reconstructed parts by default.
 - StructureFromMotion: Add support for rig of cameras
 - Support for reconstruction with projected light patterns and texturing with another set of images

Full Release Notes:
 - Viewer3D: New Trackball camera manipulator for improved navigation in the scene
 - Viewer3D: New library system to load multiple 3D objects of the same type simultaneously, simplifying results comparisons
 - Viewer3D: Add media loading overlay with BusyIndicator
 - Viewer3D: Points and cameras size are now configurable via dedicated sliders.
 - CameraInit: Add option to lock specific cameras intrinsics (if you have high-quality internal calibration information)
 - StructureFromMotion: Triangulate points if the input scene contains valid camera poses and intrinsics without landmarks
 - PrepareDenseScene: New `imagesFolders` option to override input images. This enables to use images with light patterns projected for SfM and MVS parts and do the Texturing with another set of images.
 - NodeLog: Cross-platform monospace display
 - Remove `CameraConnection` and `ExportUndistortedImages` nodes
 - Multi-machine parallelization of `PrepareDenseScene`
 - Meshing: Add option `estimateSpaceFromSfM` and observation angles check to better estimate the bounding box of the reconstruction and avoid useless reconstruction of the environment
 - Console: Filter non silenced, inoffensive warnings from QML + log Qt messages via Python logging
 - Command line (meshroom_photogrammetry): Add --pipeline parameter to use a pre-configured pipeline graph
 - Command line (meshroom_photogrammetry): Add possibility to provide pre-calibrated intrinsics.
 - Command line (meshroom_compute): Provide `meshroom_compute` executable in packaged release.
 - Image Gallery: Display Camera Intrinsics initialization status with detailed explanation, edit Sensor Database dialog, advanced menu to display view UIDs
 - StructureFromMotion: Expose advanced estimator parameters
 - FeatureMatching: Expose advanced estimator parameters
 - DepthMap: New option `exportIntermediateResults` disabled by default, so less data storage by default than before.
 - DepthMap: Use multiple GPUs by default if available and add `nbGPUs` param to limit it
 - Meshing: Add option `addLandmarksToTheDensePointCloud`
 - SfMTransform: New option to align on one specific camera
 - Graph Editor: Consistent read-only mode when computing, that can be unlocked in advanced settings
 - Graph Editor: Improved Node Menu: "duplicate"/"remove"/"delete data" with "From Here" accessible on the same entry via an additional button
 - Graph Editor: Confirmation popup before deleting node data
 - Graph Editor: Add "Clear Pending Status" action at Graph level
 - Graph Editor: Solo media in 3D viewer with Ctrl + double click on node/attribute
 - Param Editor: Fix several bugs related to attributes edition
 - Scene Compatibility: Improves detection of deeper compatibility issues, by adding an additional recursive (taking List/GroupAttributes children into account) exact description matching test when de-serializing a Node.

See [AliceVision 2.1.0 Release Notes](https://github.com/alicevision/AliceVision/blob/v2.1.0/CHANGES.md)
for more details about algorithmic changes.


## Release 2018.1.0 (2018.08.09)

 First release of Meshroom.  
 Based on [AliceVision 2.0.0](https://github.com/alicevision/AliceVision/tree/v2.0.0).
