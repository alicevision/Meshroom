import QtQuick
import Qt3D.Core 2.6
import Qt3D.Render 2.6
import Qt3D.Extras 2.15
import QtQuick.Scene3D 2.6

import "Materials"
import Utils 1.0

/**
 * MediaLoader provides a single entry point for 3D media loading.
 * It encapsulates all available plugins/loaders.
 */

 Entity {
    id: root

    property url source
    property bool loading: false
    property int status: SceneLoader.None
    property var object: null
    property int renderMode

    /// Scene's current camera
    property Camera camera: null

    property bool cached: false
    property bool cameraPickingEnabled: false

    onSourceChanged: {
        if (cached) {
            root.status = SceneLoader.Ready
            return
        }

        // Clear previously created object if any
        if (object) {
            object.destroy()
            object = null
        }

        var component = undefined
        status = SceneLoader.Loading

        if (!Filepath.exists(source)) {
            status = SceneLoader.None
            return
        }

        switch (Filepath.extension(source)) {
            case ".ply":
                if ((Filepath.extension(Filepath.removeExtension(source))) == ".pc") {
                    if (Viewer3DSettings.supportSfmData)
                        component = sfmDataLoaderEntityComponent
                }
                else {
                    component = sceneLoaderEntityComponent
                }
                break
            case ".abc": 
            case ".json":
            case ".sfm":
                if (Viewer3DSettings.supportSfmData)
                    component = sfmDataLoaderEntityComponent
                break
            case ".exr":
                if (Viewer3DSettings.supportDepthMap)
                    component = exrLoaderComponent
                break
            case ".obj":
            case ".stl":
            default:
                component = sceneLoaderEntityComponent
                break
        }

        // Media loader available
        if (component) {
            object = component.createObject(root, {"source": source})
        }
    }

    Component {
        id: sceneLoaderEntityComponent
        MediaLoaderEntity {
            id: sceneLoaderEntity
            objectName: "SceneLoader"

            components: [
                SceneLoader {
                    source: parent.source
                    onStatusChanged: function(status) {
                        if (status == SceneLoader.Ready) {
                            textureCount = sceneLoaderPostProcess(sceneLoaderEntity)
                            faceCount = Scene3DHelper.faceCount(sceneLoaderEntity)
                        }
                        root.status = status;
                    }
                }
            ]
        }
    }

    Component {
        id: sfmDataLoaderEntityComponent
        MediaLoaderEntity {
            id: sfmDataLoaderEntity
            Component.onCompleted: {
                var obj = Viewer3DSettings.sfmDataLoaderComp.createObject(sfmDataLoaderEntity, {
                                               "source": source,
                                               "fixedPointSize": Qt.binding(function() { return Viewer3DSettings.fixedPointSize }),
                                               "pointSize": Qt.binding(function() { return Viewer3DSettings.pointSize }),
                                               "locatorScale": Qt.binding(function() { return Viewer3DSettings.cameraScale }),
                                               "cameraPickingEnabled": Qt.binding(function() { return root.enabled && root.cameraPickingEnabled }),
                                               "resectionId": Qt.binding(function() { return Viewer3DSettings.resectionId }),
                                               "displayResections": Qt.binding(function() { return Viewer3DSettings.displayResectionIds }),
                                               "syncPickedViewId": Qt.binding(function() { return Viewer3DSettings.syncWithPickedViewId })
                                           });

                obj.statusChanged.connect(function() {
                    if (obj.status === SceneLoader.Ready) {
                        for (var i = 0; i < obj.pointClouds.length; ++i) {
                            vertexCount += Scene3DHelper.vertexCount(obj.pointClouds[i])
                        }
                        cameraCount = obj.spawnCameraSelectors()
                    }
                    Viewer3DSettings.resectionIdCount = obj.countResectionIds()
                    Viewer3DSettings.resectionGroups = obj.countResectionGroups(Viewer3DSettings.resectionIdCount + 1)
                    resectionIdCount = Viewer3DSettings.resectionIdCount
                    resectionGroups = Viewer3DSettings.resectionGroups
                    resectionId = Viewer3DSettings.resectionIdCount
                    root.status = obj.status
                })

                obj.cameraSelected.connect(
                    function(viewId) {
                        obj.selectedViewId = viewId
                    }
                )
            }
        }
    }

    Component {
        id: exrLoaderComponent
        MediaLoaderEntity {
            id: exrLoaderEntity
            Component.onCompleted: {
                var fSize = Filepath.fileSizeMB(source)
                if (fSize > 500) {
                    // Do not load images that are larger than 500MB
                    console.warn("Viewer3D: Do not load the EXR in 3D as the file size is too large: " + fSize + "MB")
                    root.status = SceneLoader.Error
                    return
                }

                // EXR loading strategy:
                //   - [1] as a depth map
                var obj = Viewer3DSettings.depthMapLoaderComp.createObject(
                            exrLoaderEntity, {
                                "source": source
                            })

                if (obj.status === SceneLoader.Ready) {
                    faceCount = Scene3DHelper.faceCount(obj)
                    root.status = SceneLoader.Ready
                    return
                }

                //   - [2] as an environment map
                obj.destroy()
                root.status = SceneLoader.Loading
                obj = Qt.createComponent("EnvironmentMapEntity.qml").createObject(
                            exrLoaderEntity, {
                                "source": source,
                                "position": Qt.binding(function() { return root.camera.position })
                            })
                obj.statusChanged.connect(function() {
                    root.status = obj.status;
                })
            }
        }
    }

    Component {
        id: materialSwitcherComponent
        MaterialSwitcher { }
    }

    // Remove automatically created DiffuseMapMaterial and
    // instantiate a MaterialSwitcher instead. Returns the faceCount
    function sceneLoaderPostProcess(rootEntity)
    {
        var materials = Scene3DHelper.findChildrenByProperty(rootEntity, "diffuse")
        var entities = []
        var texCount = 0
        materials.forEach(function(mat) {
            entities.push(mat.parent)
        })

        entities.forEach(function(entity) {
            var mats = []
            var componentsToRemove = []
            // Create as many MaterialSwitcher as individual materials for this entity
            // NOTE: we let each MaterialSwitcher modify the components of the entity
            //       and therefore remove the default material spawned by the sceneLoader
            for (var i = 0; i < entity.components.length; ++i)
            {
                var comp = entity.components[i]

                // Handle DiffuseMapMaterials created by SceneLoader
                if (comp.toString().indexOf("QDiffuseMapMaterial") > -1) {
                    // Store material definition
                    var m = {
                        "diffuseMap": comp.diffuse.data[0].source,
                        "shininess": comp.shininess,
                        "specular": comp.specular,
                        "ambient": comp.ambient,
                        "mode": root.renderMode
                    }
                    texCount++
                    mats.push(m)
                    componentsToRemove.push(comp)
                }

                if (comp.toString().indexOf("QPhongMaterial") > -1) {
                    // Create MaterialSwitcher with default colors
                    mats.push({})
                    componentsToRemove.push(comp)
                }
            }

            mats.forEach(function(m) {
                // Create a material switcher for each material definition
                var matSwitcher = materialSwitcherComponent.createObject(entity, m)
                matSwitcher.mode = Qt.binding(function() { return root.renderMode })
            })

            // Remove replaced components
            componentsToRemove.forEach(function(comp) {
                Scene3DHelper.removeComponent(entity, comp)
            })
        })
        return texCount
    }
}
