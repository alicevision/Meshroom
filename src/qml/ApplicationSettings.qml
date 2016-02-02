import QtQuick 2.5

Connections {
    target: null
    Component.onCompleted: {
        target.width = 800;
        target.height = 500;
        target.visible = true;
        target.color = "#111";
        target.title = "meshroom";
    }
}
