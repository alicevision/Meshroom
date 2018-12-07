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

            components: [
                CuboidMesh { xExtent: 0.2; yExtent: 0.2; zExtent: 0.2;},
                PhongMaterial{
                    id: mat
                    ambient: viewId === _reconstruction.selectedViewId ? activePalette.highlight : "#CCC"
                    diffuse: cameraPicker.containsMouse ? Qt.lighter(activePalette.highlight, 1.2) : ambient
                },
                ObjectPicker {
                    id: cameraPicker
                    enabled: root.enabled
                    onClicked: _reconstruction.selectedViewId = camSelector.viewId
                }
            ]
        }
    }
}
