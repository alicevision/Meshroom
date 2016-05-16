import QtQuick 2.5

Item {
    Connections {
        target: Qt.application
        onAboutToQuit: currentScene = defaultScene
    }
    Connections {
        target: _window
        Component.onCompleted: {
            _application.loadPlugins();
        }
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
                function _CB() {
                    currentScene.reset();
                    currentScene.setUrl(dialog.fileUrl);
                    currentScene.load();
                }
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
                if(callback) callback();
            }
            var dialog = _dialogs.saveScene.createObject(_window);
            dialog.onAccepted.connect(_CB);
            dialog.open();
        }
        onAddNode: {
            function add_CB() {
                currentScene.graph.addNode(dialog.selection, _application.nodeDescriptors[dialog.selection]);
            }
            var dialog = _dialogs.addNode.createObject(_window);
            dialog.onAccepted.connect(add_CB);
            dialog.open();
        }
    }
}
