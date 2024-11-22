import QtQuick
import Qt3D.Core 2.6
import Qt3D.Render 2.6
import Qt3D.Extras 2.15

import SfmDataEntity 1.0

/**
 * Support for SfMData files in Qt3D.
 * Create this component dynamically to test for SfmDataEntity plugin availability.
 */

SfmDataEntity {
    id: root

    property bool cameraPickingEnabled: true
    property bool syncPickedViewId: false

    // Filter out non-reconstructed cameras
    skipHidden: true

    signal cameraSelected(var viewId)

    Connections {
        target: _reconstruction
        function onSelectedViewIdChanged() {
            root.cameraSelected(_reconstruction.selectedViewId)
        }
        function onSelectedViewpointChanged() {
            root.cameraSelected(_reconstruction.pickedViewId)
        }
    }

    function spawnCameraSelectors() {
        var validCameras = 0;
        // Spawn camera selector for each camera
        for (var i = 0; i < root.cameras.length; ++i)
        {
            var cam = root.cameras[i];
            // retrieve view id
            var viewId = cam.viewId;
            if (viewId === undefined)
                continue;
            camSelectionComponent.createObject(cam, {"viewId": viewId});
            dummyCamSelectionComponent.createObject(cam, {"viewId": viewId});
            validCameras++;
        }
        return validCameras;
    }

    function countResectionIds() {
        var maxResectionId = 0
        for (var i = 0; i < root.cameras.length; i++) {
            var cam = root.cameras[i]
            var resectionId = cam.resectionId
            // 4294967295 = UINT_MAX, which might occur if the value is undefined on the C++ side
            if (resectionId === undefined || resectionId === 4294967295)
                continue
            if (resectionId > maxResectionId)
                maxResectionId = resectionId
        }

        return maxResectionId
    }


    function countResectionGroups(resectionIdCount) {
        var arr = Array(resectionIdCount).fill(0)
        for (var i = 0; i < root.cameras.length; i++) {
            var cam = root.cameras[i]
            var resectionId = cam.resectionId
            // 4294967295 = UINT_MAX, which might occur if the value is undefined on the C++ side
            if (resectionId === undefined || resectionId === 4294967295)
                continue
            arr[resectionId] = arr[resectionId] + 1
        }

        return arr
    }

    SystemPalette {
        id: activePalette
    }

    // Camera selection display only
    Component {
        id: dummyCamSelectionComponent
        Entity {
            id: dummyCamSelector
            property string viewId
            property color customColor: Qt.hsva((parseInt(viewId) / 255.0) % 1.0, 0.3, 1.0, 1.0)
            property real extent: cameraPickingEnabled ? 0.2 : 0

            components: [
                // Use cuboid to represent the camera
                Transform {
                    translation: Qt.vector3d(0, 0, 0.5 * cameraBack.zExtent)
                },
                CuboidMesh {
                    id: cameraBack
                    xExtent: parent.extent
                    yExtent: xExtent
                    zExtent: xExtent * 0.2
                },
                PhongMaterial{
                    id: mat
                    ambient: _reconstruction && (viewId === _reconstruction.selectedViewId ||
                                                 (viewId === _reconstruction.pickedViewId && syncPickedViewId)) ?
                                 activePalette.highlight : customColor  // "#CCC"
                }
            ]
        }
    }

    // Camera selection picking only
    Component {
        id: camSelectionComponent
        Entity {
            id: camSelector
            property string viewId
            property color customColor: Qt.hsva((parseInt(viewId) / 255.0) % 1.0, 0.3, 1.0, 1.0)
            property real extent: cameraPickingEnabled ? 0.5 : 0

            components: [
                // Use cuboid to represent the camera
                Transform {
                    translation: Qt.vector3d(0, 0, 0.5 * cameraBack.zExtent)
                },
                CuboidMesh {
                    id: cameraBack
                    xExtent: parent.extent
                    yExtent: xExtent
                    zExtent: xExtent
                },
                ObjectPicker {
                    id: cameraPicker
                    property point pos
                    onPressed: function(pick) {
                        pos = pick.position;
                        pick.accepted = (pick.buttons & Qt.LeftButton) && cameraPickingEnabled
                    }
                    onReleased: function(pick) {
                        const delta = Qt.point(Math.abs(pos.x - pick.position.x), Math.abs(pos.y - pick.position.y))
                        // Only trigger picking when mouse has not moved between press and release
                        if (delta.x + delta.y < 4) {
                            _reconstruction.selectedViewId = camSelector.viewId
                        }
                    }
                }
            ]
        }
    }
}
