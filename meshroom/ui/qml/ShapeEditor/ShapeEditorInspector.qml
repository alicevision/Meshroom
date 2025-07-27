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
    anchors.margins: 0
    padding: 5
    radius: 0
    width: 200

    ColumnLayout {
        anchors.fill: parent
        spacing: 5

        // header
        RowLayout {
            // pane title
            Label {
                text: "Shape Inspector"
                font.bold: true
                Layout.fillWidth: true
            }

            // minimize or maximize button
            MaterialToolButton {
                id: bodyButton
                text: shapeInspectorBody.visible ? MaterialIcons.arrow_drop_down : MaterialIcons.arrow_drop_up
                font.pointSize: 10
                ToolTip.text: shapeInspectorBody.visible ? "Minimize" : "Maximize"
                onClicked: { shapeInspectorBody.visible = !shapeInspectorBody.visible }
            }
        }

        // body
        ColumnLayout {
            id: shapeInspectorBody
            spacing: 2

            RowLayout {
                Layout.topMargin: 5
                Layout.bottomMargin: 5
                Label {
                    text: "Node Parameters"
                    font.pointSize: 8
                    font.bold: true
                }
            }

            // current node parameters shapes
            ShapeListInspector {
                model: ShapeEditor.nodeShapeList
            }

            // current node files shape lists
            Repeater {
                model: ShapeEditor.nodeFileShapeLists
                delegate: ColumnLayout {
                    spacing: 2

                    RowLayout {
                        Layout.topMargin: 8
                        Layout.bottomMargin: 5
                        MaterialLabel {
                            font.pointSize: 10
                            text: MaterialIcons.insert_drive_file
                        }
                        Label {
                            text: shapeListName
                            font.pointSize: 8
                            font.bold: true
                        }
                    }

                    ShapeListInspector { 
                        model: shapeListModel
                    }
                }
            }
        }
    }
}