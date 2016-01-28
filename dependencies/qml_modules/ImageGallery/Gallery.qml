import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import QtQml.Models 2.2
import DarkStyle.Controls 1.0
import DarkStyle 1.0
import "delegate"
import "views"

Item {

    id: root
    property variant model: null
    property bool editable: true

    DropArea {
        anchors.fill: parent
        enabled: root.editable
        onFilesDropped: {
            for(var i=0; i<files.length; ++i) {
                var ext = files[i].split('.').pop().toUpperCase();
                if(ext == "JPG" || ext == "JPEG")
                    model.addResource(files[i]);
            }
        }
    }

    QtObject {
        id: _selector
        signal refreshSelectionFlags()
        property variant selection: []
        property int lastSelected: -1
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
            model.removeResource(model.get(id).modelData);
        }
    }

    TabView {
        id: tabview
        anchors.fill: parent
        focus: true
        DelegateModel {
            id: imageModel
            delegate: ImageDelegate {
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
        Tab {
            title: "Grid"
            property string iconSource: "qrc:///images/grid.svg"
            GridImageView { visualModel: imageModel }
        }
        Tab {
            title: "List"
            property string iconSource: "qrc:///images/diaporama.svg"
            ListImageView { visualModel: imageModel }
        }
        Tab {
            title: "Detail"
            property string iconSource: "qrc:///images/list.svg"
            DetailedImageView  { visualModel: imageModel }
        }
    }

    Item {
        anchors.top: parent.top
        anchors.right: parent.right
        width: 30 * listview.count
        height: 30
        Rectangle {
            anchors.fill: parent
            opacity: 0.6
            color: Style.window.color.xdark
        }
        ListView {
            id: listview
            anchors.fill: parent
            model: tabview.count
            spacing: 0
            interactive: false
            orientation: Qt.Horizontal
            delegate: Button {
                iconSource: tabview.getTab(index).iconSource
                onClicked: tabview.currentIndex = index
            }
        }
    }

}
