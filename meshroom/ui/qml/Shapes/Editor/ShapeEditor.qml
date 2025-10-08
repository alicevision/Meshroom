import QtQuick
import QtQuick.Layouts
import QtQuick.Controls

/**
* ShapeEditor
*
* @biref A component to display and edit the shape attributes and shape files 
*        of the current node.
* @param model - the given current node list of attributes
* @param filterText - the given label filter string
*/
Item {
    id: shapeEditor

    // Properties
    property alias model: attributeslist.model
    property string filterText: ""

    Pane {
        anchors.fill: parent
        anchors.margins: 2
        padding: 5
        background: Rectangle { color: Qt.darker(parent.palette.window, 1.4) }

        ScrollView {
            anchors.fill: parent

            // Disable horizontal scrolling
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

            // Ensure that vertical scrolling is always enabled when necessary
            ScrollBar.vertical.policy: ScrollBar.AlwaysOn
            ScrollBar.vertical.visible: contentHeight > height
        
            ColumnLayout {
                anchors.fill: parent
                spacing: 0

                // Shape attributes
                ListView {
                    id: attributeslist
                    spacing: 0
                    interactive: false

                    // Layout
                    Layout.fillWidth: true
                    Layout.preferredHeight: contentHeight

                    delegate: ShapeEditorItem {
                        model: object
                        active: object.hasDisplayableShape && object.matchText(filterText)
                        width: ListView.view.width 
                    }
                }

                // Shape files
                ListView {
                    spacing: 0
                    interactive: false

                    // Layout
                    Layout.fillWidth: true
                    Layout.preferredHeight: contentHeight

                    model: ShapeFilesHelper.nodeShapeFiles
                    delegate: ShapeEditorItem { 
                        model: object
                        width: ListView.view.width
                    }
                }
            }

            // Reset selection
            TapHandler {
                acceptedButtons: Qt.LeftButton
                gesturePolicy: TapHandler.WithinBounds
                onTapped: { ShapeViewerHelper.selectedShapeName = "" }
            }
        }
    }
}
