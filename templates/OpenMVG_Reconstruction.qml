import QtQuick 2.7
import QtQuick.Layouts 1.3
import QtQuick.Controls 2.0
import NodeEditor 1.0
import FontAwesome 1.0

RowLayout {
    id: root

    EditAttributeDelegate {
        id: imageAD
        Layout.topMargin: 10
        graph: templateManager.graph
        nodeName: "openmvg.imageListing1"
        attributeName: "files"
        Layout.columnSpan: 2
        Layout.fillWidth: true
        Layout.fillHeight: true
        onStatusChanged: {
            if(status == Loader.Ready)
            {
                item.thumbnailSize = 175
            }
        }
        Connections {
            target: imageAD.attribute
            //onValueChanged: // TODO: instantiate voctree if attribute.length is big
        }
        Label {
            anchors.centerIn: parent
            font.family: FontAwesome.fontFamily
            visible: imageAD.attribute.value.length == 0
            text: FontAwesome.fileImageO + " Drop Images (.jpg, .jpeg, .png)"
        }
    }

    Rectangle {
        color: "#232323"
        Layout.fillHeight: true
        Layout.topMargin: 30; Layout.bottomMargin: 30
        Layout.leftMargin: 15; Layout.rightMargin: 15
        Layout.minimumHeight: 10
        implicitWidth: 1
    }

    GridLayout {
        id: parameters
        columns: 2
        Layout.alignment: Qt.AlignTop
        Layout.topMargin: 10
        columnSpacing: 14

        Label {
            text: FontAwesome.wrench + "  Parameters "
            font.family: FontAwesome.fontFamily
            Layout.columnSpan: 2
            Layout.bottomMargin: 30
            Layout.alignment: Qt.AlignHCenter
        }

        Label {
            text: "Density"
            state: "small"
        }

        EditAttributeDelegate {
            graph: templateManager.graph
            nodeName: "openmvg.featureExtraction1"
            attributeName: "describerPreset"
        }

        Label {
            text: "Feature Type"
            state: "small"
        }

        EditAttributeDelegate {
            graph: templateManager.graph
            nodeName: "openmvg.featureExtraction1"
            attributeName: "describerMethod"
        }

        CheckBox {
            id: meshingCB
            Layout.columnSpan: 2
            text: "Meshing"
            property bool hasMeshing: templateManager.graph.nodes.count && templateManager.graph.nodes.rowIndex("openmvg.exportForMeshing") > 0
            checked: hasMeshing
            property point refPos: templateManager.graph.nodeByName("openmvg.structureFromMotion1").position
            property variant meshingGraph: {
                "nodes": [
                            {
                                "type": "openmvg.ExportForMeshing",
                                "name": "openmvg.exportForMeshing",
                                "x": refPos.x + 130,
                                "y": refPos.y + 50
                            },
                            {
                                "type": "openmvg.Meshing",
                                "name": "openmvg.meshing",
                                "x": refPos.x + 130*2,
                                "y": refPos.y + 50
                            }
                        ],
                 "edges": [
                            {
                                "plug": "sfmdata",
                                "source": "openmvg.structureFromMotion1",
                                "target": "openmvg.exportForMeshing"
                            },
                            {
                                "plug": "input",
                                "source": "openmvg.exportForMeshing",
                                "target": "openmvg.meshing"
                            }
                        ]
            }

            onClicked: {
                if(!hasMeshing)
                {
                    templateManager.scene.undoStack.beginMacro("Enabled Meshing")
                    templateManager.graph.deserializeFromJSON(meshingGraph);
                    templateManager.scene.undoStack.endMacro()
                }
                else
                {
                    templateManager.scene.undoStack.beginMacro("Disable Meshing")
                    meshingGraph["nodes"].forEach(function(node) {
                        templateManager.graph.removeNode(node);
                    })
                    templateManager.scene.undoStack.endMacro()
                }
            }
        }
        Loader {
            id: meshingLoader
            active: meshingCB.hasMeshing
            Layout.columnSpan: 2
            Layout.fillWidth: true
            Layout.leftMargin: 10
            Layout.rightMargin: 10
            visible: active

            sourceComponent: Component {
                GridLayout {
                    columns: 2
                    columnSpacing: parameters.columnSpacing
                    Label {
                        text: "Scale"
                        state: "small"
                        Layout.fillWidth: true
                    }

                    EditAttributeDelegate {
                        graph: templateManager.graph
                        nodeName: "openmvg.exportForMeshing"
                        attributeName: "scale"
                    }
                }
            }
        }

        CheckBox {
            onClicked: nodeEditor.visible = !nodeEditor.visible
            text: "[DEBUG] Show Graph"
        }

        NodeEditor {
            id: nodeEditor
            Layout.columnSpan: 2
            Layout.fillHeight: true
            Layout.fillWidth: true
            visible: false
            graph: templateManager.graph
        }

    }
}
