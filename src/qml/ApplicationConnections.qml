import QtQuick 2.5

Item {
    Connections {
        target: Qt.application
        onAboutToQuit: currentScene.reset()
    }
    Connections {
        target: _window
        onNewScene: {
            function reset_CB() { currentScene.reset(); }
            if(currentScene.dirty) {
                function save_CB() { saveScene(reset_CB); }
                var dialog = _dialogs.maySaveScene.createObject(_window);
                dialog.onAccepted.connect(save_CB);
                dialog.onRejected.connect(reset_CB);
                dialog.open();
                return;
            }
            reset_CB();
        }
        onOpenScene: {
            function open_CB() {
                function _CB() { addScene(dialog.fileUrl); }
                var dialog = _dialogs.openScene.createObject(_window);
                dialog.onAccepted.connect(_CB);
                dialog.open();
            }
            if(currentScene.dirty) {
                function save_CB() { saveScene(open_CB); }
                var dialog = _dialogs.maySaveScene.createObject(_window);
                dialog.onAccepted.connect(save_CB);
                dialog.onRejected.connect(open_CB);
                dialog.open();
                return;
            }
            open_CB();
        }
        onSaveScene: {
            if(!currentScene.url.toString()) {
                saveAsScene(callback);
                return;
            }
            currentScene.save();
            if(callback) callback();
        }
        onSaveAsScene: {
            function _CB() {
                currentScene.setUrl(dialog.fileUrl);
                currentScene.save();
                addScene(dialog.fileUrl);
                if(callback) callback();
            }
            var dialog = _dialogs.saveScene.createObject(_window);
            dialog.onAccepted.connect(_CB);
            dialog.open();
        }
        onAddScene: {
            _application.scenes.addScene(url);
            currentScene = _application.scenes.get(_application.scenes.count-1).modelData;
            currentScene.load();
        }
        onSelectScene: {
            function select_CB() {
                currentScene = _application.scenes.get(id).modelData;
                currentScene.load();
            }
            if(currentScene.dirty) {
                function save_CB() { saveScene(select_CB); }
                var dialog = _dialogs.maySaveScene.createObject(_window);
                dialog.onAccepted.connect(save_CB);
                dialog.onRejected.connect(select_CB);
                dialog.open();
                return;
            }
            select_CB();
        }
        onAddNode: {
            function add_CB() { currentScene.graph.addNode(dialog.selection); }
            var dialog = _dialogs.addNode.createObject(_window);
            dialog.onAccepted.connect(add_CB);
            dialog.open();
        }
    }
}
