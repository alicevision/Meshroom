import meshViewer

import QtQuick
import QtQuick.Controls

SceneView {
    id: sceneView
    anchors.fill: parent
    focus: true

    cameraInfo.fov: 70.0

    layers: [
        AxisLayer { 
        },
        GridLayer {
            id: gridLayer
            minorFadeStartPixels: 1
            minorFadeEndPixels: 3
            minorOpacity: 0.45
            minorLineWidth: 1.1
        },
        MeshLayer {
            id: meshLayer
            mesh: sceneMesh
            picking: true

            /*onSelectionChanged: {
                const updatedPositions = sphereLayer.positions.slice()
                updatedPositions.push(selection)
                sphereLayer.positions = updatedPositions
            }*/
        },
        SphereLayer {
            id: sphereLayer
        }
    ]

    MeshObject {
        id: sceneMesh
        source: Qt.resolvedUrl("/s/prods/mvg/_source_global/users/servantf/meshviewer/mesh.obj")
    }

    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.MiddleButton

        property real initialX: 0
        property real initialY: 0

        onClicked: (mouse) => {
            if (mouse.button === Qt.LeftButton)
            {
                sceneView.pick(Qt.vector2d(mouse.x, mouse.y))
            }
        }

        onPressed: (mouse) => {
            initialX = mouse.x
            initialY = mouse.y
        }

        onReleased: (mouse) => {
            if (mouse.modifiers & Qt.AltModifier)
            {
                sceneView.motionInfo.applyTransform()
            }
        }

        onPositionChanged: (mouse) => {
            if (!(mouse.modifiers & Qt.AltModifier))
            {
                return
            }

            const deltaX = mouse.x - initialX
            const deltaY = mouse.y - initialY

            if (mouse.buttons & Qt.LeftButton)
            {
                sceneView.motionInfo.relativeRotationX = deltaY * 0.5
                sceneView.motionInfo.relativeRotationY = deltaX * 0.5
            }
            else if (mouse.buttons & Qt.MiddleButton)
            {
                sceneView.motionInfo.planeX = deltaX * 0.01
                sceneView.motionInfo.planeY = deltaY * 0.01
            }
            else if (mouse.buttons & Qt.RightButton)
            {
                sceneView.motionInfo.distance = deltaY * 0.2;
            }
        }

    }
}