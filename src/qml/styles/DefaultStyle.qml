import QtQuick 2.5
import QtQuick.Controls.Styles 1.4

QtObject {
    id: root
    property QtObject text: QtObject {
        property QtObject size: QtObject {
            property int xsmall: 9;
            property int small: 10;
            property int normal: 12;
            property int large: 16;
            property int xlarge: 24;
        }
        property QtObject color: QtObject {
            property color xlighter: Qt.lighter(normal, 3);
            property color lighter: Qt.lighter(normal, 2);
            property color normal: "#DDD";
            property color darker: Qt.darker(normal, 2);
            property color xdarker: Qt.darker(normal, 3);
            property color disabled: "#444";
            property color selected: "#5BB1F7";
        }
    }
    property QtObject icon: QtObject {
        property QtObject size: QtObject {
            property int xsmall: 14;
            property int small: 18;
            property int normal: 24;
            property int large: 32;
            property int xlarge: 50;
        }
    }
    property QtObject log: QtObject {
        property QtObject color: QtObject {
            property color debug: "#444";
            property color info: "#666";
            property color warning: "#DAA520";
            property color critical: "red";
            property color fatal: "red";
        }
    }
    property QtObject window: QtObject {
        property QtObject color: QtObject {
            property color xlighter: Qt.lighter(normal, 1.8);
            property color lighter: Qt.lighter(normal, 1.4);
            property color normal: "#393939";
            property color darker: Qt.darker(normal, 1.4);
            property color xdarker: Qt.darker(normal, 1.8);
            property color selected: "#5BB1F7";
        }
    }
    property Component bggl: ApplicationWindowStyle {
        background: Item {} // hide default application background
    }
    property Component bg: ApplicationWindowStyle {
        background: Rectangle { color: root.window.color.darker }
    }
}
