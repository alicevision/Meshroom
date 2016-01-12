import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import DarkStyle.Controls 1.0
import DarkStyle 1.0
import "../../../../delegates"

Rectangle {

    id: root

    color: Style.window.color.normal

    property real thumbnailSize: 130
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

    DropArea {
        anchors.fill: parent
        onFilesDropped: {
            for(var i=0; i<files.length; ++i) {
                var ext = files[i].split('.').pop().toUpperCase();
                if(ext == "JPG" || ext == "JPEG")
                    currentJob.images.addResource(files[i]);
            }
        }
    }

    Item {
        anchors.fill: parent
        clip: true
        GridView {
            id: grid
            anchors.fill: parent
            anchors.margins: 10
            cellWidth: root.thumbnailSize
            cellHeight: root.thumbnailSize
            model: currentJob.images
            onCountChanged: {
                clearSelection();
                refreshAllInitialPairIndicators();
            }
            delegate: ImageDelegate {
                width: GridView.view.cellWidth
                height: GridView.view.cellHeight
                enabled: root.enabled
                onItemToggled: {
                    selectionStartItem = index;
                    if(doClear)
                        clearSelection();
                    selected = (toggleSelection(index)<0)?false:true;
                }
                onViewInFullscreen: {
                    fullscreenImage.source = url;
                }
                onPerformMultiSelection: {
                    if(selectionStartItem < 0)
                        selectionStartItem = index;
                    for(var i=Math.min(selectionStartItem, index); i <= Math.max(selectionStartItem, index); i++)
                        addToSelection(i);
                    refreshAllSelectionIndicators();
                }
            }
        }
        Item {
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.rightMargin: 30
            width: 150
            height: 30
            Rectangle {
                anchors.fill: parent
                opacity: 0.6
                color: Style.window.color.xdark
            }
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 4
                anchors.rightMargin: 4
                spacing: 0
                Slider {
                    Layout.fillWidth: true
                    minimumValue: 100
                    maximumValue: 500
                    value: 130
                    onValueChanged: root.thumbnailSize = value
                }
                // ToolButton {
                //     iconSource: "qrc:///images/disk.svg"
                // }
            }
        }
    }

    Rectangle {
        anchors.fill: parent
        color: "black"
        enabled: (fullscreenImage.source == "") ? false : true;
        opacity: (fullscreenImage.source == "") ? 0 : 1;
        Behavior on opacity { NumberAnimation {} }
        Image {
            id: fullscreenImage
            anchors.fill: parent
            source: ""
            fillMode: Image.PreserveAspectFit
        }
        MouseArea {
            anchors.fill: parent
            onClicked: {
                fullscreenImage.source = "";
            }
        }
    }

    Component.onCompleted: forceActiveFocus()
    Keys.onPressed: {
        if((event.key == Qt.Key_Delete) || (event.key == Qt.Key_Backspace))
            removeSelectedResources();
        if((event.key == Qt.Key_A) && (event.modifiers & Qt.ControlModifier)) {
            selectAll();
            refreshAllSelectionIndicators();
        }
    }

}
