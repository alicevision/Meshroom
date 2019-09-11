import Qt3D.Core 2.0
import Qt3D.Render 2.0

Material {
    id: root

    property color ambient: Qt.rgba( 0.05, 0.05, 0.05, 1.0 )
    property color diffuse: Qt.rgba( 0.7, 0.7, 0.7, 1.0 )
    property color specular: Qt.rgba( 0.95, 0.95, 0.95, 1.0 )
    property real shininess: 1.0
    property real lineWidth: 0.8
    property color lineColor: Qt.rgba( 0.2, 0.2, 0.2, 1.0 )
    property vector3d lightIntensity: Qt.vector3d(0.7, 0.7, 0.7)
    property vector4d lightPosition:  Qt.vector4d(0.0, 0.0, 0.0, 1.0)

    effect: WireframeEffect {}

    parameters: [
        Parameter { name: "ka"; value: Qt.vector3d(root.ambient.r, root.ambient.g, root.ambient.b) },
        Parameter { name: "kd"; value: Qt.vector3d(root.diffuse.r, root.diffuse.g, root.diffuse.b) },
        Parameter { name: "ksp"; value: Qt.vector3d(root.specular.r, root.specular.g, root.specular.b) },
        Parameter { name: "shininess"; value: root.shininess },
        Parameter { name: "line.width"; value: root.lineWidth },
        Parameter { name: "line.color"; value: root.lineColor },
        Parameter { name: "light.intensity"; value: root.lightIntensity },
        Parameter { name: "light.position"; value: root.lightPosition }
    ]
}
