import QtQuick 2.11
import QtQuick.Controls 2.4
import QtQuick.Layouts 1.11
import Utils 1.0

// Read-only list of images
FocusScope {
    id: root

    property var imgs
    property string currentImg

    height: parent.height

    function forceActiveFocus() {
        list.forceActiveFocus()
    }

    Component {
        id: listItemDelegate

        Rectangle {
            id: rect
            width: 500
            height: 100
            color: Qt.darker(activePalette.window, 1.1)
            border.color: Qt.darker(activePalette.highlight)
            border.width: listItemMA.containsMouse ? 2 : 0

            property alias filepath: pathLabel.text
            
            MouseArea {
                id: listItemMA
                anchors.fill: parent
                hoverEnabled: true
                acceptedButtons: Qt.LeftButton | Qt.RightButton
                onPressed: {
                    if (mouse.button == Qt.LeftButton)
                        list.currentIndex = index
                }

                RowLayout {
                    width: parent.width
                    height: parent.height

                    Column {
                        Label { 
                            text: modelData.name
                            width: parent.width-100
                        }
                        Label { 
                            id: pathLabel
                            text: modelData.path 
                            width: parent.width-100
                        }
                    }
                    Image {
                        Layout.alignment: Qt.AlignRight
                        Layout.margins: 5
                        source: modelData.path 
                        sourceSize.width: 90
                        asynchronous: true
                        autoTransform: true
                        fillMode: Image.PreserveAspectFit
                    }
                }
            }
        }
    }
        
    ListView {
        id: list

        height: parent.height
        width: 510
        focus: true
        clip: true
        highlightFollowsCurrentItem: true
        keyNavigationEnabled: true
        currentIndex: 0  
        
        onCurrentItemChanged: {
            root.currentImg = 'file:///'+currentItem.filepath
        }

        highlight: Component {
            Rectangle {
                color: activePalette.highlight
                opacity: 0.3
                z: 2
            }
        }
        highlightMoveDuration: 0
        highlightResizeDuration: 0

        ScrollBar.vertical: ScrollBar { 
            active: true
            minimumSize: 0.05 
        }

        model: imgs
        delegate: listItemDelegate
    }
}