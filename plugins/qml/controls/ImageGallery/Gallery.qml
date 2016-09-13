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
    property bool editable: true
    property bool closeable: false

    // signal / slots
    signal closed()
    signal itemAdded(var item)
    signal itemRemoved(var item)

    // selection functions
    QtObject {
        id: _selector
        signal refreshSelectionFlags()
        property variant selection: []
        property int lastSelected: 0
        function add(id) {
            lastSelected = id;
            var index = selection.indexOf(id);
            if(index>=0)
                return;
            selection.push(id);
            refreshSelectionFlags();
        }
        function selectOne(id) {
            clear();
            add(id);
            refreshSelectionFlags();
        }
        function selectContiguous(id) {
            if(lastSelected < 0) {
                selectOne(id);
                return;
            }
            var start = Math.min(lastSelected, id);
            var end = Math.max(lastSelected, id);
            for(var i=start; i <= end; i++)
                add(i);
            refreshSelectionFlags();
        }
        function unselect(id) {
            lastSelected = -1;
            var index = selection.indexOf(id);
            if(index>=0)
                selection.splice(index, 1);
            refreshSelectionFlags();
        }
        function isSelected(id) {
            return (selection.indexOf(id)>=0);
        }
        function clear() {
            selection = [];
            refreshSelectionFlags();
        }
        function remove() {
            // sort numerically and descending, then remove
            selection.sort(function(a,b){return b - a});
            for(var i=0; i<selection.length; ++i)
                removeOne(selection[i]);
            clear();
        }
        function removeOne(id) {
            root.itemRemoved(model[id]);
        }
    }

    // drop area in background
    DropArea {
        anchors.fill: parent
        enabled: root.editable
        onDropped: {
            for(var i=0; i<drop.urls.length; ++i)
                root.itemAdded(drop.urls[i]);
        }
    }

    // visual model
    DelegateModel {
        id: imageModel
        delegate: ThumbnailDelegate {
            editable: root.editable
            onSelectOne: _selector.selectOne(id)
            onSelectContiguous: _selector.selectContiguous(id)
            onSelectExtended: _selector.add(id)
            onUnselect: _selector.unselect(id)
            onUnselectAll: _selector.clear()
            onRemoveSelected: _selector.remove()
            onRemoveOne: _selector.removeOne(id)
        }
        model: root.model
    }

    ColumnLayout {
        anchors.fill: parent
        ColumnLayout {
            spacing: 0
            TabBar {
                id: bar
                Layout.fillWidth: true
                TabButton { text: "Grid" }
                TabButton { text: "List" }
            }
            StackLayout {
                currentIndex: bar.currentIndex
                onCurrentIndexChanged: children[currentIndex].focus = true
                GridImageView { visualModel: imageModel }
                ListImageView { visualModel: imageModel }
            }
        }
    }

}
