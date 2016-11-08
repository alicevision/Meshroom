import QtQuick 2.7
import QtQuick.Layouts 1.3
import QtQuick.Controls 2.0
import Meshroom.Scene 1.0
import Logger 1.0
import NodeEditor 1.0
import "controls"

ApplicationWindow {

    id: _window

    // parameters
    width: 800
    height: 500
    visible: true

    // properties
    property variant currentScene: _application.scene
    property variant currentNode: null
    property variant defaultScene: Scene {} // used when application is
                                            // about to quit

    // actions
    signal newScene()
    signal openScene()
    signal importScene(string url)
    signal saveScene(var callback)
    signal saveSceneAs(var callback)
    signal addScene(string url)
    signal selectScene(int id)
    signal addNode()
    signal editSettings()
    signal displayAttribute(var attribute)
    signal displayIn3DView(var attribute)
    signal displayIn2DView(var attribute)

    // connections, menus and dialogs
    ApplicationConnections {}
    ApplicationMenus {}
    ApplicationDialogs { id: _dialogs }

    // header
    header: Header {}

    SplitView {
        anchors.fill: parent
        orientation: Qt.Horizontal
        initialOffset: 0.75
        minimumSize: 30
        first: SplitView {
            id: splitview
            orientation: Qt.Vertical
            initialOffset: 0.5
            minimumSize: 31
            first: Item {
                anchors.fill: parent
                property variant selectedView: view3D
                Connections {
                    target: _window
                    onDisplayAttribute: {
                        switch(attribute.type) {
                            case Attribute.IMAGELIST:
                                selectedView = view2D
                                displayIn2DView(attribute)
                                break;
                            case Attribute.OBJECT3D:
                                selectedView = view3D
                                displayIn3DView(attribute)
                                break;
                            default:
                                selectedView = defaultView
                                break;
                        }
                    }
                }
                View2D {
                    id: view2D
                    anchors.fill: parent
                    visible: selectedView == view2D
                }
                View3D {
                    id: view3D
                    anchors.fill: parent
                    visible: selectedView == view3D
                }
                Item {
                    id: defaultView
                    anchors.fill: parent
                    visible: selectedView == defaultView
                    Label {
                        anchors.centerIn: parent
                        horizontalAlignment: Text.AlignHCenter
                        text: "no suitable view available"
                        enabled: false
                    }
                }
            }
            second: Graph { onSelectionChanged: currentNode = node }
        }
        second: Settings { model: currentNode }
    }

    // footer
    footer: LogBar {
        expandIcon: expanded ? "qrc:///images/shrink.svg" : "qrc:///images/expand.svg"
        trashIcon: "qrc:///images/trash.svg"
    }

}
