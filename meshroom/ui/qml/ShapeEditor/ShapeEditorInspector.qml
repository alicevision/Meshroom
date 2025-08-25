import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import MaterialIcons 2.2
import Controls 1.0
import Utils 1.0

/**
* ShapeEditor Inspector
*
* @biref A small pane to control current node shape parameters and shape files.
*/
FloatingPane {
    id: root

    // pane properties
    padding: 4
    anchors.fill: parent
    anchors.leftMargin: 0

    // scroll view
    ScrollView {
        id: inspectorScrollView
        anchors.fill: parent

        // disable horizontal scroll
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

        // main column layout
        ColumnLayout {
            width: root.width - inspectorScrollView.effectiveScrollBarWidth // leave some space for scroll bar
            spacing: 2

            // current node shapes lists
            Repeater {
                model: ShapeEditor.nodeShapeLists
                delegate: ColumnLayout {
                    spacing: 2

                    // shape list section label
                    Label {
                        Layout.fillWidth: true
                        padding: 2
                        background: Rectangle { color: parent.palette.mid }
                        text: shapeListName
                    }
                    
                    // shape list parameters 
                    ShapeListInspector { 
                        model: shapeListModel
                    }
                }
            }
        }
    }
}