import QtQuick 2.2
import QtQuick.Controls 1.3
import QtQuick.Layouts 1.1

import "delegates"
import "../styles"

Item {
    id: root

    property variant model: null // resources model
    property bool selectable: false

    function getSelectionList() {
        var selectionList = [];
        for(var i = root.model.resources.length; i > 0 ; i--) {
            if(grid.contentItem.children[i-1].selected) {
                selectionList.push(root.model.resources[i-1].url);
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
                cellWidth: 120
                cellHeight: 120
                model: root.model ? root.model.resources : 0
                delegate: ResourceGridDelegate {
                    onItemClicked: {
                        if(!root.selectable)
                            return;
                        toggleSelectedState();
                    }
                    onItemDoubleClicked: {
                        if(!root.selectable)
                            return;
                        if(modelData.isDir())
                            return;
                    }
                }
                clip: true
            }
        }
    }
}
