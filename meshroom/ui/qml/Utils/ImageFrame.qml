import QtQuick 2.9
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3
import Utils 1.0

// Item for images
Item {
    id: root

    property string path
    property string fname
    property string description
    property bool isCurrentItem: false
    property var adt
    property var gridy
    property var doubleclickcreate

    signal pressed(var mouse)

    Frame {
        anchors.fill: parent
        MouseArea {
            id: imageMA
            height: 125
            width: 160
            hoverEnabled: true
            acceptedButtons: Qt.LeftButton | Qt.RightButton
            onPressed: {
                if (mouse.button == Qt.LeftButton)
                    gridy.unselectAll()
                    root.isCurrentItem = root.isCurrentItem ? false : true
                    root.adt.selectedName = root.fname
                    root.adt.text = description
                    gridy.focus = true
                root.pressed(mouse)
            }
            onDoubleClicked: {
                if (mouse.button == Qt.LeftButton)
                    doubleclickcreate(fname)
            }

            ColumnLayout {
                anchors.fill: parent
                spacing: 0

                // Image thumbnail and background
                Column {
                    Rectangle {
                        id: imageBackground
                        color: Qt.darker(imageLabel.palette.base, 1.15)
                        height: 125
                        width: 160
                        border.color: root.isCurrentItem ? imageLabel.palette.highlight : Qt.darker(imageLabel.palette.highlight)
                        border.width: imageMA.containsMouse || root.isCurrentItem ? 2 : 0
                        Image {
                            id: img
                            anchors.left: parent.left
                            anchors.leftMargin: 5
                            anchors.top: parent.top
                            anchors.topMargin: 5
                            source: "../../img/"+root.path
                            sourceSize: Qt.size(150, 150)
                            asynchronous: true
                            autoTransform: true
                        }
                        Rectangle {
                            color: root.isCurrentItem ? imageLabel.palette.highlight : parent.color
                            height: 30
                            width: parent.width
                            anchors.bottom: parent.bottom
                            anchors.bottomMargin: 2
                            anchors.left: parent.left
                            anchors.leftMargin: 2
                            anchors.right: parent.right
                            anchors.rightMargin: 2
                            // Image basename
                            Label {
                                id: imageLabel
                                Layout.fillWidth: true
                                padding: 8
                                font.pointSize: 8
                                anchors.bottom: parent.bottom
                                horizontalAlignment: Text.AlignHCenter
                                text: root.fname
                            }
                        }
                    }
                }
            }
        }
    }
}