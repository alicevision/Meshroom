import QtQuick 2.9
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3
import Utils 1.0


/**
 * ImageDelegate for a Viewpoint object.
 */
Item {
    id: root

    property variant viewpoint
    property bool isCurrentItem: false
    property alias source: _viewpoint.source
    property alias metadata: _viewpoint.metadata
    property bool readOnly: false
    property bool displayViewId: false

    signal pressed(var mouse)
    signal removeRequest()

    default property alias children: imageMA.children

    // retrieve viewpoints inner data
    QtObject {
        id: _viewpoint
        property url source: viewpoint ? Filepath.stringToUrl(viewpoint.get("path").value) : ''
        property int viewId: viewpoint ? viewpoint.get("viewId").value : -1
        property string metadataStr: viewpoint ? viewpoint.get("metadata").value : ''
        property var metadata: metadataStr ? JSON.parse(viewpoint.get("metadata").value) : {}
    }

    MouseArea {
        id: imageMA
        anchors.fill: parent
        anchors.margins: 6
        hoverEnabled: true
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        onPressed: {
            if (mouse.button == Qt.RightButton)
                imageMenu.popup()
            root.pressed(mouse)
        }

        Menu {
            id: imageMenu
            MenuItem {
                text: "Show Containing Folder"
                onClicked: {
                    Qt.openUrlExternally(Filepath.dirname(root.source))
                }
            }
            MenuItem {
                text: "Remove"
                enabled: !root.readOnly
                onClicked: removeRequest()
            }
            MenuItem {
                text: "Define As Center Image"
                property var activeNode: _reconstruction.activeNodes.get("SfMTransform").node
                enabled: !root.readOnly && _viewpoint.viewId != -1 && _reconstruction && activeNode
                onClicked: activeNode.attribute("transformation").value = _viewpoint.viewId.toString()
            }
        }

        ColumnLayout {
            anchors.fill: parent
            spacing: 0

            // Image thumbnail and background
            Rectangle {
                id: imageBackground
                color: Qt.darker(imageLabel.palette.base, 1.15)
                Layout.fillHeight: true
                Layout.fillWidth: true
                border.color: isCurrentItem ? imageLabel.palette.highlight : Qt.darker(imageLabel.palette.highlight)
                border.width: imageMA.containsMouse || root.isCurrentItem ? 2 : 0
                Image {
                    anchors.fill: parent
                    anchors.margins: 4
                    source: root.source
                    sourceSize: Qt.size(100, 100)
                    asynchronous: true
                    autoTransform: true
                    fillMode: Image.PreserveAspectFit
                }
            }
            // Image basename
            Label {
                id: imageLabel
                Layout.fillWidth: true
                padding: 2
                font.pointSize: 8
                elide: Text.ElideMiddle
                horizontalAlignment: Text.AlignHCenter
                text: Filepath.basename(root.source)
                background: Rectangle {
                    color: root.isCurrentItem ? parent.palette.highlight : "transparent"
                }
            }

            // Image viewId
            Loader {
                active: displayViewId
                Layout.fillWidth: true
                visible: active
                sourceComponent: Label {
                    padding: imageLabel.padding
                    font.pointSize: imageLabel.font.pointSize
                    elide: imageLabel.elide
                    horizontalAlignment: imageLabel.horizontalAlignment
                    text: _viewpoint.viewId
                    background: Rectangle {
                        color: imageLabel.background.color
                    }
                }
            }
        }
    }
}
