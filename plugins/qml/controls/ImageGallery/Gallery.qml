import QtQuick 2.7
import QtQuick.Controls 2.0
import QtQuick.Layouts 1.3
import QtQml.Models 2.2
import "delegate"
import "views"

Item {

    id: root
    implicitWidth: 200
    implicitHeight: 200

    // properties
    property variant model: null
    property Item background: null
    property url gridIcon: ""
    property url listIcon: ""

    // signal / slots
    signal closed()
    signal itemAdded(var urls)
    signal itemRemoved(var urls)

    // selection functions
    QtObject {
        id: _selector
        signal refreshSelectionFlags()
        property variant selection: []
        property int lastSelected: 0
        function addToSelection(id) {
            lastSelected = id;
            var index = selection.indexOf(id);
            if(index>=0)
                return;
            selection.push(id);
        }
        function removeFromSelection(id) {
            lastSelected = id;
            var index = selection.indexOf(id);
            if(index>=0)
                selection.splice(index, 1);
        }
        function clearSelection() {
            selection = [];
        }
        function selectOne(id) {
            clearSelection();
            addToSelection(id);
        }
        function selectContiguous(id) {
            if(lastSelected < 0) {
                selectOne(id);
                return;
            }
            var start = Math.min(lastSelected, id);
            var end = Math.max(lastSelected, id);
            for(var i=start; i <= end; i++)
                addToSelection(i);
        }
        function isSelected(id) {
            return (selection.indexOf(id)>=0);
        }
    }

    onBackgroundChanged: {
        for(var i = dropArea.children.length; i > 0 ; i--)
            dropArea.children[i-1].destroy()
        background.parent = dropArea
        background.anchors.fill = dropArea
    }

    // drop area in background
    DropArea {
        id: dropArea
        anchors.fill: parent
        onDropped: root.itemAdded(drop.urls);
        opacity: containsDrag ? 1 : 0
        Behavior on opacity { NumberAnimation {} }
    }

    // visual model
    DelegateModel {
        id: imageModel
        delegate: ThumbnailDelegate {
            onSelectOne: {
                _selector.selectOne(id)
                _selector.refreshSelectionFlags()
            }
            onSelectContiguous: {
                _selector.selectContiguous(id)
                _selector.refreshSelectionFlags()
            }
            onSelectExtended: {
                _selector.addToSelection(id)
                _selector.refreshSelectionFlags()
            }
            onUnselect: {
                _selector.removeFromSelection(id)
                _selector.refreshSelectionFlags()
            }
            onUnselectAll: {
                _selector.clearSelection()
                _selector.refreshSelectionFlags()
            }
            onRemoveSelected: {
                var list = []
                for(var i=0; i<_selector.selection.length; ++i)
                    list.push(root.model[_selector.selection[i]])
                root.itemRemoved(list);
                _selector.clearSelection();
                _selector.refreshSelectionFlags()
            }
            onRemoveOne: {
                root.itemRemoved([root.model[id]])
                _selector.clearSelection();
                _selector.refreshSelectionFlags()
            }
        }
        model: root.model
    }


    ColumnLayout {
        anchors.fill: parent

        // views
        StackLayout {
            id: stack
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: 0
            onCurrentIndexChanged: children[currentIndex].focus = true
            GridImageView {
                id: gridImageView
                visualModel: imageModel
            }
            ListImageView {
                id: listImageView
                visualModel: imageModel
            }
        }

        // footer
        Item {
            Layout.fillWidth: true
            Layout.preferredHeight: 20
            Rectangle {
                anchors.fill: parent
                color: Qt.rgba(0, 0, 0, 0.6)
            }
            RowLayout {
                anchors.fill: parent
                spacing: 0
                ToolButton {
                    Layout.preferredHeight: 20
                    Layout.preferredWidth: 20
                    onClicked: stack.currentIndex = 0
                    Component.onCompleted: {
                        if(typeof icon == "undefined") return;
                        icon = root.gridIcon
                    }
                }
                ToolButton {
                    Layout.preferredHeight: 20
                    Layout.preferredWidth: 20
                    onClicked: stack.currentIndex = 1
                    Component.onCompleted: {
                        if(typeof icon == "undefined") return;
                        icon = root.listIcon
                    }
                }
                Item {
                    Layout.fillWidth: true
                }
                Label {
                    Layout.alignment: Qt.AlignRight
                    Layout.rightMargin: 4
                    text: root.model.length + ((root.model.length<=1) ? " image" : " images")
                    state: "xsmall"
                }
            }
        }

    }

    // thumbnail size -/+
    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.NoButton
        property double factor: 1.1
        onWheel: {
            if(wheel.modifiers != Qt.ControlModifier) {
                wheel.accepted = false
                return;
            }
            var zoomFactor = wheel.angleDelta.y > 0 ? factor : 1/factor
            var thumbSize = gridImageView.thumbnailSize*zoomFactor;
            if(thumbSize <= 20 || thumbSize > 150)
                return;
            gridImageView.thumbnailSize = thumbSize;
            listImageView.thumbnailSize = thumbSize;
            wheel.accepted = true;
        }
    }
}
