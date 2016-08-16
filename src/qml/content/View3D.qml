import QtQuick 2.7
import QtQuick.Scene3D 2.0

import Qt3D.Core 2.0
import Qt3D.Render 2.0
import Qt3D.Input 2.0
import Qt3D.Extras 2.0
import Qt3D.Logic 2.0

Scene3D {
    id: scene3d

    anchors.fill: parent
    focus: true
    aspects: ["input", "logic"]
    cameraAspectRatioMode: Scene3D.AutomaticAspectRatio

    Entity {
        id: sceneRoot
        Camera {
            id: camera
            property vector3d frontNormalized: position.minus(viewCenter).normalized()
            projectionType: CameraLens.PerspectiveProjection
            fieldOfView: 45
            nearPlane : 0.1
            farPlane : 1000.0
            position: Qt.vector3d( 0.0, 0.0, 40.0 )
            upVector: Qt.vector3d( 0.0, 1.0, 0.0 )
            viewCenter: Qt.vector3d( 0.0, 0.0, 0.0 )
        }

        components: [
            RenderSettings {
                activeFrameGraph: ForwardRenderer {
                    clearColor: Qt.rgba(0, 0, 0, 0.2)
                    camera: camera
                }
            },
            InputSettings {}
        ]
        MouseDevice { id:mouse1 }
        MouseHandler {
            sourceDevice: mouse1
            onWheel: {
                var d = wheel.angleDelta.y * 0.1
                camera.fieldOfView = camera.fieldOfView+d
                console.log("camera.fieldOfView = %1".arg(camera.fieldOfView))
            }
        }
        KeyboardDevice { id: keyboard1 }
		KeyboardHandler {
			id: input
			sourceDevice: keyboard1
			focus: true
			onPressed: {
				switch (event.key) {
					case Qt.Key_W: {
						movement.w = camera.frontNormalized
						break
					}
					case Qt.Key_S: {
						movement.s = camera.frontNormalized
						break
					}
					case Qt.Key_A: {
						movement.a = camera.frontNormalized.crossProduct(camera.upVector).normalized()
						break
					}
					case Qt.Key_D: {
						movement.d = camera.frontNormalized.crossProduct(camera.upVector).normalized()
						break
					}
					case Qt.Key_Shift: {
						movement.acc = .2
						break
					}
				}
			}
			onReleased: {
				switch (event.key) {
					case Qt.Key_W: {
						movement.w = movement.zero
						break
					}
					case Qt.Key_S: {
						movement.s = movement.zero
						break
					}
					case Qt.Key_A: {
						movement.a = movement.zero
						break
					}
					case Qt.Key_D: {
						movement.d = movement.zero
						break
					}
					case Qt.Key_Shift: {
						movement.acc = 1.
						break
					}
				}
			}
		}
        FrameAction {
			id: movement
			readonly property real scale: 1e1
			property real acc: 1.
			property vector3d w: Qt.vector3d(0,0,0)
			property vector3d s: Qt.vector3d(0,0,0)
			property vector3d a: Qt.vector3d(0,0,0)
			property vector3d d: Qt.vector3d(0,0,0)
			property vector3d velocity: w.minus(s).plus(a).minus(d)
			readonly property vector3d zero: Qt.vector3d(0,0,0)
			onTriggered: {
				if (velocity !== zero) {
					camera.translate(velocity.times(acc * scale * dt))
					console.log("camera.viewCenter = %1".arg(camera.viewCenter))
				}
			}
		}
        PhongMaterial {
            id: material
        }
        SphereMesh {
            id: sphereMesh
            radius: 3
        }
        Transform {
            id: sphereTransform
            property real userAngle: 0.0
            matrix: {
                var m = Qt.matrix4x4();
                m.rotate(userAngle, Qt.vector3d(0, 1, 0))
                // m.translate(Qt.vector3d(20, 0, 0));
                return m;
            }
        }
        Entity {
            id: sphereEntity
            components: [ sphereMesh, material, sphereTransform ]
        }
    }

}
