import QtQuick 2.9
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3
import Utils 1.0


/**
 * ImageDelegate for a Viewpoint object.
 */
Item {
    id: imageDelegate

    property variant viewpoint
    property bool isCurrentItem: false
    property alias source: _viewpoint.source
    property alias metadata: _viewpoint.metadata

    signal pressed(var mouse)
    signal removeRequest()

    // retrieve viewpoints inner data
    QtObject {
        id: _viewpoint
        property string source: viewpoint ? viewpoint.get("path").value : ''
        property string metadataStr: viewpoint ? viewpoint.get("metadata").value : ''
        property var metadata: metadataStr ? JSON.parse(viewpoint.get("metadata").value) : null
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
            imageDelegate.pressed(mouse)
        }

        Menu {
            id: imageMenu
            MenuItem {
                text: "Show Containing Folder"
                onClicked: {
                    Qt.openUrlExternally(Filepath.dirname(imageDelegate.source))
                }
            }
            MenuItem {
                text: "Remove"
                enabled: !root.readOnly
                onClicked: removeRequest()
            }
        }

        ColumnLayout {
            anchors.fill: parent
            spacing: 0

            // Image thumbnail and background
            Rectangle {
                id: imageBackground
                color: Qt.darker(palette.base, 1.15)
                Layout.fillHeight: true
                Layout.fillWidth: true
                border.color: isCurrentItem ? palette.highlight : Qt.darker(palette.highlight)
                border.width: imageMA.containsMouse || imageDelegate.isCurrentItem ? 2 : 0
                Image {
                    anchors.fill: parent
                    anchors.margins: 4
                    source: Filepath.stringToFile(imageDelegate.source)
                    sourceSize: Qt.size(100, 100)
                    asynchronous: true
                    autoTransform: true
                    fillMode: Image.PreserveAspectFit
                }
            }
            // Image basename
            Label {
                Layout.fillWidth: true
                padding: 2
                font.pointSize: 8
                elide: Text.ElideMiddle
                horizontalAlignment: Text.AlignHCenter
                text: Filepath.basename(imageDelegate.source)
                background: Rectangle {
                    color: imageDelegate.isCurrentItem ? palette.highlight : "transparent"
                }
            }
        }
    }
}
