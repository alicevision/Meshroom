import QtQuick 2.5

import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import Popart 0.1 // Shortcuts

import "../delegates"

Item {
    id: root
    property real thumbnailSize: 100
    property variant selection: []
    property int selectionStartItem: -1

    function toggleSelection(resourceId) {
        var index = selection.indexOf(resourceId);
        if(index<0) {
            selection.push(resourceId);
            return selection.length-1;
        } else {
            selection.splice(index, 1);
            return -1;
        }
    }
    function addToSelection(resourceId) {
        var index = selection.indexOf(resourceId);
        if(index>=0)
            return;
        selection.push(resourceId);
    }
    function selectAll(resourceId) {
        selection = [];
        for(var i=0; i<grid.count; ++i)
            selection.push(i);
    }
    function isSelected(resourceId) {
        return (selection.indexOf(resourceId)>=0);
    }
    function clearSelection() {
        selection = [];
        for(var i=0; i<grid.contentItem.children.length; ++i)
            grid.contentItem.children[i].selected = false;
    }
    function removeSelectedResources() {
        // sort numerically and descending, then remove
        selection.sort(function(a,b){return b - a});
        for(var i=0; i<selection.length; ++i)
            currentJob.images.removeResource(currentJob.images.data(currentJob.images.index(selection[i], 0), 259));
    }
    function refreshAllInitialPairIndicators() {
        for(var i=0; i<grid.contentItem.children.length; ++i) {
            if(grid.contentItem.children[i].objectName == "resourceDelegate")
                grid.contentItem.children[i].refreshInitialPairIndicators();
        }
    }
    function refreshAllSelectionIndicators() {
        for(var i=0; i<grid.contentItem.children.length; ++i) {
            if(grid.contentItem.children[i].objectName == "resourceDelegate")
                grid.contentItem.children[i].refreshSelectionState();
        }
    }

    GridView {
        id: grid
        anchors.fill: parent
        cellWidth: root.thumbnailSize
        cellHeight: root.thumbnailSize
        model: currentJob.images
        onCountChanged: {
            clearSelection();
            refreshAllInitialPairIndicators();
        }
        delegate: ResourceGridDelegate {
            Component.onCompleted: selected = isSelected(index)
            enabled: root.enabled
            onItemToggled: {
                selectionStartItem = index;
                if(doClear)
                    clearSelection();
                selected = (toggleSelection(index)<0)?false:true;
            }
            onItemDropped: refreshAllInitialPairIndicators();
            onPerformMultiSelection: {
                if(selectionStartItem < 0)
                    selectionStartItem = index;
                for(var i=Math.min(selectionStartItem, index); i <= Math.max(selectionStartItem, index); i++)
                    addToSelection(i);
                refreshAllSelectionIndicators();
            }
        }
        clip: true
    }
    CustomSlider {
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        width: 70
        minimumValue: 100
        maximumValue: 500
        value: 100
        onValueChanged: root.thumbnailSize = value
    }
    Shortcut {
        key: "Backspace"
        onActivated: removeSelectedResources()
    }
    Shortcut {
        key: "Delete"
        onActivated: removeSelectedResources()
    }
    Shortcut {
        key: "Ctrl+A"
        onActivated: {
            selectAll();
            refreshAllSelectionIndicators();
        }
    }
}
