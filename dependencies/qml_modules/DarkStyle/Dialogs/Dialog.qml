import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Layouts 1.2
import "../Controls"
import ".."


Item {

    id: root

    property string title: "?"
    property string backgroundColor: Style.window.color.dark
    property Component content: null
    property int contentMinimumWidth: 400
    property int contentMinimumHeight: 300

    signal open()
    signal accept()
    signal reject()

    onOpen: visible = true
    onAccept: destroy()
    onReject: destroy()

    implicitWidth: parent.width
    implicitHeight: parent.height
    visible: false

    Rectangle {
        // layer.enabled: true
        // layer.effect: ShaderEffect {
        //     id: shader
        //     property real test: 0.2
        //     SequentialAnimation {
        //         running: true
        //         loops: Animation.Infinite
        //         NumberAnimation { target: shader; property: "test"; to: 1.0; duration: 1000 }
        //         NumberAnimation { target: shader; property: "test"; to: 0.2; duration: 1000 }
        //     }
        //     fragmentShader: "
        //     #version 330
        //     uniform lowp float test;
        //     uniform lowp sampler2D source; // this item
        //     uniform lowp float qt_Opacity; // inherited opacity of this item
        //     in highp vec2 qt_TexCoord0;
        //     out vec4 fragColor;
        //     void main() {
        //         lowp vec4 p = texture(source, qt_TexCoord0);
        //         lowp vec3 g = p.xyz * (vec3(0.8, 0.2, 0.0)*test);
        //         fragColor = vec4(g.r, g.g, g.b, p.a) * qt_Opacity;
        //     }"
        // }
        anchors.fill: parent
        color: Style.window.color.xdark
        opacity: 0.7
        Image {
            anchors.fill: parent
            source: "qrc:///images/stripes.png"
            fillMode: Image.Tile
            opacity: 0.3
        }
        MouseArea {
            anchors.fill: parent
            hoverEnabled: true
        }
    }
    Item {
        anchors.centerIn: parent
        width: Math.min(parent.width * 0.6, root.contentMinimumWidth)
        height: Math.min(parent.height * 0.6, root.contentMinimumHeight)
        Rectangle {
            anchors.fill: parent
            color: root.backgroundColor
            opacity: 0.9
        }
        ToolButton {
            anchors.top: parent.top
            anchors.right: parent.right
            iconSource: "qrc:///images/close.svg"
            onClicked: root.reject()
        }
        ColumnLayout {
            anchors.fill: parent
            spacing: 0
            RowLayout {
                width: parent.width
                height: 30
                Item {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 30
                    Text {
                        anchors.fill: parent
                        anchors.leftMargin: 10
                        text: root.title
                    }
                }
            }
            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Loader {
                    anchors.fill: parent
                    anchors.topMargin: 20
                    anchors.leftMargin: 10
                    anchors.rightMargin: 10
                    anchors.bottomMargin: 20
                    sourceComponent: root.content
                }
            }
        }
    }
}
