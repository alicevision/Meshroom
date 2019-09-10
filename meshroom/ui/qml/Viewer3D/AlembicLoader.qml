import AlembicEntity 2.0
import QtQuick 2.9
import Qt3D.Core 2.1
import Qt3D.Render 2.1
import Qt3D.Extras 2.1

/**
 * Support for Alembic files in Qt3d.
 * Create this component dynamically to test for AlembicEntity plugin availability.
 */
AlembicEntity {
    id: root

    property bool cameraPickingEnabled: true
    // filter out non-reconstructed cameras
    skipHidden: true

    signal cameraSelected(var viewId)

    function spawnCameraSelectors() {
        var validCameras = 0;
        // spawn camera selector for each camera
        for(var i = 0; i < root.cameras.length; ++i)
        {
            var cam = root.cameras[i];
            // retrieve view id
            var viewId = cam.userProperties["mvg_viewId"];
            if(viewId === undefined)
                continue;
            camSelectionComponent.createObject(cam, {"viewId": viewId});
            validCameras++;
        }
        return validCameras;
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
            // Qt 5.13: binding cameraPicker.enabled to cameraPickerEnabled
            //          causes rendering issues when entity gets disabled.
            //          set CuboidMesh extent to 0 to disable picking.
            property real extent: cameraPickingEnabled ? 0.2 : 0

            components: [
                CuboidMesh { xExtent: parent.extent; yExtent: xExtent; zExtent: xExtent },
                PhongMaterial{
                    id: mat
                    ambient: viewId === _reconstruction.selectedViewId ? activePalette.highlight : "#CCC"
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
                        if(delta.x + delta.y < 4)
                        {
                            _reconstruction.selectedViewId = camSelector.viewId;
                        }
                    }
                }
            ]
        }

    }
}
