import QtQuick 2.5

Connections {
    target: null
    Component.onCompleted: {
        target.width = 400;
        target.height = 300;
        target.visible = true;
        target.color = "#111";
    }
}
