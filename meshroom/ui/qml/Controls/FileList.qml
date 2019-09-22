import QtQuick 2.11
import QtQuick.Controls 2.4
import QtQuick.Layouts 1.11
import Utils 1.0

// Read-only list of files
FocusScope {
    id: root

    property var files
    property string currentFile: 'file:///'+list.currentItem.path

    width: parent.width
    height: parent.height

    function forceActiveFocus() {
        list.forceActiveFocus()
    }

    Component {
        id: listItemDelegate

        Rectangle {
            id: rect
            width: parent.width-10
            height: nameLabel.height
            color: Qt.darker(activePalette.window, 1.1)
            border.color: Qt.darker(activePalette.highlight)
            border.width: listItemMA.containsMouse ? 2 : 0

            property string path: modelData.path
            
            MouseArea {
                id: listItemMA
                anchors.fill: parent
                hoverEnabled: true
                acceptedButtons: Qt.LeftButton | Qt.RightButton
                onPressed: {
                    if (mouse.button == Qt.LeftButton)
                        list.currentIndex = index
                }

                Label { 
                    id: nameLabel
                    text: modelData.name
                    width: parent.width
                }
            }
        }
    }
        
    ListView {
        id: list

        height: parent.height
        width: parent.width
        focus: true
        clip: true
        highlightFollowsCurrentItem: true
        keyNavigationEnabled: true
        currentIndex: 0  

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

        model: files
        delegate: listItemDelegate
    }
}