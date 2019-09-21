import QtQuick 2.12
import Qt3D.Core 2.12
import Qt3D.Render 2.12


/**
 * ViewpointCamera sets up a Camera to match a Viewpoint's internal parameters.
 */
Entity {
    id: root

    property variant viewpoint

    property Camera camera: Camera {

        nearPlane : 0.1
        farPlane : 10000.0
        viewCenter: Qt.vector3d(0.0, 0.0, -1.0)

        // Scene light, attached to the camera
        Entity {
            components: [
                PointLight {
                    color: "white"
                }
            ]
        }
    }

    components: [
        Transform {
            id: transform

            Behavior on rotation {
                PropertyAnimation { duration: 200}
            }
            Behavior on translation {
                Vector3dAnimation { duration: 200}
            }
        }
    ]

    StateGroup {
        states: [
            State {
                name: "valid"
                when: root.viewpoint !== null
                PropertyChanges {
                    target: camera
                    fieldOfView: root.viewpoint.fieldOfView
                    upVector: root.viewpoint.upVector
                }
                PropertyChanges {
                    target: transform
                    rotation: root.viewpoint.rotation
                    translation: root.viewpoint.translation
                }
            }
        ]
    }

}
