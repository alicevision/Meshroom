import SfmDataEntity 1.0
import QtQuick 2.15
import Qt3D.Core 2.15
import Qt3D.Render 2.15
import Qt3D.Extras 2.15

/**
 * Support for SfMData files in Qt3D.
 * Create this component dynamically to test for SfmDataEntity plugin availability.
 */
SfmDataEntity {
    id: root

    property bool cameraPickingEnabled: true
    // filter out non-reconstructed cameras
    skipHidden: true

    signal cameraSelected(var viewId)

    Connections {
        target: _reconstruction
        function onSelectedViewIdChanged() {
            root.cameraSelected(_reconstruction.selectedViewId)
        }
    }

    function spawnCameraSelectors() {
        var validCameras = 0;
        // spawn camera selector for each camera
        for (var i = 0; i < root.cameras.length; ++i)
        {
            var cam = root.cameras[i];
            // retrieve view id
            var viewId = cam.viewId;
            if (viewId === undefined)
                continue;
            camSelectionComponent.createObject(cam, {"viewId": viewId});
            validCameras++;
        }
        return validCameras;
    }

    function countResectionIds() {
        var maxResectionId = 0
        for (var i = 0; i < root.cameras.length; i++) {
            var cam = root.cameras[i]
            var resectionId = cam.resectionId
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
            if (resectionId === undefined || resectionId === 4294967295)
                continue
            arr[resectionId] = arr[resectionId] + 1
        }

        return arr
    }

    SystemPalette {
        id: activePalette
    }

    // Camera selection picking and display
    Component {
        id: camSelectionComponent
        Entity {
            id: camSelector
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
                    ambient: _reconstruction && viewId === _reconstruction.selectedViewId ? activePalette.highlight : customColor // "#CCC"
                    diffuse: cameraPicker.containsMouse ? Qt.lighter(activePalette.highlight, 1.2) : ambient
                },
                ObjectPicker {
                    id: cameraPicker
                    property point pos
                    onPressed: {
                        pos = pick.position;
                        pick.accepted = (pick.buttons & Qt.LeftButton) && cameraPickingEnabled
                    }
                    onReleased: {
                        const delta = Qt.point(Math.abs(pos.x - pick.position.x), Math.abs(pos.y - pick.position.y));
                        // only trigger picking when mouse has not moved between press and release
                        if (delta.x + delta.y < 4)
                        {
                            _reconstruction.selectedViewId = camSelector.viewId;
                        }
                    }
                }
            ]
        }
    }
}
