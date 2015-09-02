import QtQuick 2.2
import QtQuick.Controls 1.3
import QtQuick.Layouts 1.1

import "../delegates"
import "../styles"

Item {
    id: root

    property variant jobModel: null
    property real thumbnailSize: 120
    property bool selectable: false

    function getSelectionList() {
        var selectionList = [];
        for(var i = root.jobModel.resources.length; i > 0 ; i--) {
            if(grid.contentItem.children[i-1].selected) {
                selectionList.push(root.jobModel.resources[i-1].url);
            }
        }
        return selectionList;
    }

    RowLayout {
        anchors.fill: parent
        spacing: 0

        // gallery
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
            GridView {
                id: grid
                anchors.fill: parent
                cellWidth: root.thumbnailSize
                cellHeight: root.thumbnailSize
                model: root.jobModel ? root.jobModel.resources : 0
                delegate: ResourceGridDelegate {
                    onItemToggled: {
                        if(!root.selectable)
                            return;
                        toggleSelectedState();
                    }
                    onItemDeleted: root.jobModel.removeResources(root.jobModel.resources[index])
                    onInitialPairASetted: root.jobModel.setPairA(url)
                    onInitialPairBSetted: root.jobModel.setPairB(url)
                }
                clip: true
            }
        }
    }
    Slider {
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        width: 50
        height: 10
        minimumValue: 100
        maximumValue: 300
        value: 120
        onValueChanged: root.thumbnailSize = value
    }
}
