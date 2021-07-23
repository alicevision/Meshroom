# Meshroom Changelog

For algorithmic changes related to the photogrammetric pipeline, 
please refer to [AliceVision changelog](https://github.com/alicevision/AliceVision/blob/develop/CHANGES.md).

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
