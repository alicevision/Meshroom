import QtQuick 2.2
import QtQuick.Controls 1.2
import QtQuick.Controls.Styles 1.3
import QtQuick.Layouts 1.1

ToolButton {
    id: root
    property string hoverIconSource: ""
    property int iconSize: _style.icon.size.normal
    property bool highlighted: false
    onHoveredChanged: z = hovered ? 1 : 0
    style: ButtonStyle {
        panel: Item {
            implicitHeight: root.iconSize
            implicitWidth: root.iconSize
            Image {
                id: icon
                sourceSize: Qt.size(root.iconSize, root.iconSize)
                source: (control.hovered && root.hoverIconSource) ? root.hoverIconSource : control.iconSource
                smooth: true
                opacity: control.hovered ? 0.4 : 1
                // layer.enabled: root.highlighted
                // layer.effect: ShaderEffect {
                //     fragmentShader: "#version 330
                //         uniform lowp sampler2D source; // this item
                //         uniform lowp float qt_Opacity; // inherited opacity of this item
                //         varying highp vec2 qt_TexCoord0;
                //         void main() {
                //             lowp vec4 p = texture2D(source, qt_TexCoord0);
                //             // lowp vec3 g = p.xyz * vec3(0.356, 0.694, 0.969);
                //             lowp vec3 g = p.xyz * vec3(0.01, 0.9, 0.01);
                //             gl_FragColor = vec4(g.r, g.g, g.b, p.a) * qt_Opacity;
                //         }"
                // }
            }
            Rectangle {
                anchors.centerIn: icon
                width: title.width + 4
                height: parent.height
                radius: 4
                color: _style.window.color.xdarker
                opacity: control.hovered ? 0.5 : 0
                visible: control.text.length >= 1
                Behavior on opacity { NumberAnimation{} }
            }
            CustomText {
                id: title
                anchors.centerIn: icon
                visible: control.hovered
                text: control.text
                textSize: _style.text.size.xsmall
                color: _style.text.color.normal
                opacity: control.hovered ? 1 : 0
                Behavior on opacity { NumberAnimation{} }
            }
        }
    }
}
