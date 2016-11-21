import QtQuick 2.7

Item {
    Connections {
        target: Qt.application
        onAboutToQuit: currentScene = defaultScene
    }
    Connections {
        target: _window
        onNewScene: {
            function reset_CB() { currentScene.reset(); }
            if(!currentScene.undoStack.isClean) {
                function save_CB() { saveScene(reset_CB); }
                var dialog = _dialogs.maySaveScene.createObject(_window.contentItem);
                dialog.onAccepted.connect(save_CB);
                dialog.onRejected.connect(reset_CB);
                dialog.open();
                return;
            }
            reset_CB();
        }
        onOpenScene: {
            function open_CB() {
                function _CB() { currentScene.load(dialog.fileUrl); }
                var dialog = _dialogs.openScene.createObject(_window.contentItem);
                dialog.onAccepted.connect(_CB);
                dialog.open();
            }
            if(!currentScene.undoStack.isClean) {
                function save_CB() { saveScene(open_CB); }
                var dialog = _dialogs.maySaveScene.createObject(_window.contentItem);
                dialog.onAccepted.connect(save_CB);
                dialog.onRejected.connect(open_CB);
                dialog.open();
                return;
            }
            open_CB();
        }
        onImportTemplate: {
            function import_CB(selection) {
                importScene(selection);
            }
            var dialog = _dialogs.importTemplate.createObject(_window.contentItem);
            dialog.onAccepted.connect(import_CB);
            dialog.open();
        }
        onImportScene: {
            currentScene["import"](url);
        }
        onSaveScene: {
            if(!currentScene.url.toString()) {
                saveSceneAs(callback);
                return;
            }
            currentScene.save();
            if(callback) callback();
        }
        onSaveSceneAs: {
            function _CB() {
                currentScene.saveAs(dialog.fileUrl);
                if(callback) callback();
            }
            var dialog = _dialogs.saveScene.createObject(_window.contentItem);
            dialog.onAccepted.connect(_CB);
            dialog.open();
        }
        onAddNode: {
            function add_CB(selection) {
                currentScene.graph.addNode(selection);
            }
            var dialog = _dialogs.addNode.createObject(_window.contentItem);
            dialog.onAccepted.connect(add_CB);
            dialog.open();
        }
        onEditSettings: {
            var dialog = _dialogs.sceneSettings.createObject(_window.contentItem);
            dialog.open();
        }
    }
}
