# Meshroom Changelog

For algorithmic changes related to the photogrammetric pipeline, 
please refer to [AliceVision changelog](https://github.com/alicevision/AliceVision/blob/develop/CHANGES.md).

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
