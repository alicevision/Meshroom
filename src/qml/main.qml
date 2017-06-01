import QtQuick 2.7
import QtQuick.Layouts 1.3
import QtQuick.Controls 2.0
import QtQuick.Controls 1.4 as Controls1
import QtQuick.Controls.Styles 1.4 as Controls1Styles
import QtQuick.Dialogs 1.2
import Meshroom.Scene 1.0
import Logger 1.0
import NodeEditor 1.0
import FontAwesome 1.0
import "controls"

Controls1.ApplicationWindow {

    id: _window

    // parameters
    width: 1280
    height: 720
    visible: true

    // properties
    property variant currentScene: _application.scene
    property variant currentNode: null
    property variant defaultScene: Scene {} // used when application is
                                            // about to quit

    // actions
    signal newScene()
    signal openScene()
    signal openRecentScene()
    signal importTemplate()
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
    ApplicationDialogs { id: _dialogs }

    style: Controls1Styles.ApplicationWindowStyle {
        background: Rectangle {
            color: "#171719"
        }
    }

    menuBar: ApplicationMenu {}

    title: {
        var t = "";
        if(currentScene.name)
        {
            t += currentScene.name;
            if(!currentScene.undoStack.isClean)
                t += "*";
            t += " - ";
        }
        t += "Meshroom";
        return t;
    }

    CustomSplitView {
        id: mainSplitView
        anchors.fill: parent
        orientation: Qt.Horizontal

        GraphsList {
            id: graphsList
            Layout.fillHeight: true
            Layout.minimumWidth: 20
            implicitWidth: 180
            scene: currentScene

            onAddGraphRequest: homePageOverlay.show("NEW")
        }

        CustomSplitView {
            Layout.fillHeight: true
            Layout.fillWidth: true
            Layout.minimumWidth: 30

            orientation: Qt.Vertical
            Item {
                id: viewsContainer
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.minimumHeight: 50
                property variant selectedView: view3D

                property variant node: currentScene.graph.activeNode
                property variant attribute: {
                    if(!node)
                        return undefined
                    return node.outputs.data(node.outputs.index(0,0), AttributeCollection.ModelDataRole);
                }
                onAttributeChanged: {
                    if(!attribute)
                    {
                        displayIn3DView(undefined)
                        return
                    }
                    switch(attribute.type) {
                        case Attribute.IMAGELIST:
                            viewsContainer.selectedView = view2D
                            displayIn2DView(attribute)
                            break;
                        case Attribute.OBJECT3D:
                            viewsContainer.selectedView = view3D
                            displayIn3DView(attribute)
                            break;
                        default:
                            viewsContainer.selectedView = defaultView
                            break;
                    }
                }

                View2D {
                    id: view2D
                    anchors.fill: parent
                    visible: parent.selectedView == view2D
                }
                View3D {
                    id: view3D
                    anchors.fill: parent
                    visible: parent.selectedView == view3D
                }
                Item {
                    id: defaultView
                    anchors.fill: parent
                    visible: parent.selectedView == defaultView
                    Label {
                        anchors.centerIn: parent
                        horizontalAlignment: Text.AlignHCenter
                        text: "no suitable view available"
                        enabled: false
                    }
                }
            }
            Graph {
                Layout.fillWidth: true
                Layout.minimumHeight: 10
                implicitHeight: _window.height * 0.4
                onSelectionChanged: currentNode = node
            }
        }
        Settings {
            Layout.fillHeight: true
            implicitWidth: _window.width * 0.2
            graph: currentScene.graph
            node: currentNode
        }
    }

    // Overlay for HomePage
    MouseArea {
        id: homePageOverlay
        anchors.fill: parent
        hoverEnabled: true
        onDoubleClicked: display = false
        property bool display: false
        visible: display || !currentScene.url.toString()

        function show(state)
        {
            display = true;
            if(state)
                homePage.state = state
        }

        Connections {
            target: _application.scene
            onGraphChanged: homePageOverlay.display = false
        }

        Rectangle {
            anchors.fill: parent
            color: Qt.darker("#EE171719", 1.5)
            Rectangle {
                anchors.fill: parent
                anchors.margins: 20
                color: "#171719"
                border.color: "#444"
                MouseArea { anchors.fill: parent; acceptedButtons: Qt.AllButtons }
                HomePage {
                    id: homePage
                    anchors.fill: parent
                }
            }
        }
    }

    // footer
    statusBar: LogBar {
        expandIcon: expanded ? "qrc:///images/shrink.svg" : "qrc:///images/expand.svg"
        trashIcon: "qrc:///images/trash.svg"
    }

}
