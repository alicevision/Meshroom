pragma Singleton
import QtQuick 2.5

QtObject {
    property QtObject text: QtObject {
        property QtObject size: QtObject {
            property int xsmall: 9;
            property int small: 12;
            property int normal: 14;
            property int large: 18;
            property int xlarge: 22;
        }
        property QtObject color: QtObject {
            property color xlight: Qt.lighter(normal, 3);
            property color light: Qt.lighter(normal, 2);
            property color normal: "#DDD";
            property color dark: Qt.darker(normal, 2);
            property color xdark: Qt.darker(normal, 3);
            property color disabled: "#444";
            property color selected: "#5BB1F7";
            property color debug: "#444";
            property color info: "#666";
            property color warning: "#DAA520";
            property color critical: "red";
            property color fatal: "red";
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
    property QtObject window: QtObject {
        property QtObject color: QtObject {
            property color xlight: Qt.lighter(normal, 3.5);
            property color light: Qt.lighter(normal, 1.4);
            property color normal: "#393939";
            property color dark: Qt.darker(normal, 1.4);
            property color xdark: Qt.darker(normal, 2.5);
            property color selected: "#5BB1F7";
        }
    }
}
