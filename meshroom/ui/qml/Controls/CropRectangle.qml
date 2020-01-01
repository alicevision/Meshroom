import QtQuick 2.9
import QtQuick.Controls 2.3


/**
 * Dragable rectangle to select part of a image.
 */
Rectangle {
    id: root
    color: "#354682B4"

    property int rulersSize: 18

    border {
        width: 2
        color: "steelblue"
    }

    MouseArea {     // drag mouse area
        anchors.fill: parent
        drag{
            target: parent
            minimumX: 0
            minimumY: 0
            maximumX: parent.parent.width - parent.width
            maximumY: parent.parent.height - parent.height
        }
    }

    Rectangle {
        width: rulersSize
        height: rulersSize
        radius: rulersSize
        color: rulerMA1.drag.active ? Qt.lighter("steelblue", 1.2) : "steelblue"
        border.color: Qt.lighter("steelblue", 1.2)
        border.width: rulerMA1.containsMouse ? 2 : 0
        anchors.horizontalCenter: parent.left
        anchors.verticalCenter: parent.verticalCenter

        MouseArea {
            id: rulerMA1
            anchors.fill: parent
            hoverEnabled: true
            drag{ target: parent; axis: Drag.XAxis }
            onMouseXChanged: {
                if (drag.active) {
                    root.width = root.width - mouseX
                    if (root.width < 50) {
                        root.width = 50
                    } else {
                        root.x = root.x + mouseX
                    }

                    if (root.x < 0) {
                        root.x = 0
                        root.width = root.width + mouseX
                    }
                }
            }
        }
    }

    Rectangle {
        width: rulersSize
        height: rulersSize
        radius: rulersSize
        color: rulerMA2.drag.active ? Qt.lighter("steelblue", 1.2) : "steelblue"
        border.color: Qt.lighter("steelblue", 1.2)
        border.width: rulerMA2.containsMouse ? 2 : 0
        anchors.horizontalCenter: parent.left
        anchors.verticalCenter: parent.top

        MouseArea {
            id: rulerMA2
            anchors.fill: parent
            hoverEnabled: true
            drag{ target: parent; axis: Drag.XAndYAxis }
            onMouseYChanged: {
                if (drag.active) {
                    root.width = root.width - mouseX
                    if (root.width < 50) {
                        root.width = 50
                    } else {
                        root.x = root.x + mouseX
                    }

                    root.height = root.height - mouseY
                    if (root.height < 50) {
                        root.height = 50
                    } else {
                        root.y = root.y + mouseY
                    }

                    if (root.x < 0) {
                        root.x = 0
                        root.width = root.width + mouseX
                    }

                    if (root.y < 0) {
                        root.y = 0
                        root.height = root.height + mouseY
                    }
                }
            }
        }
    }

    Rectangle {
        width: rulersSize
        height: rulersSize
        radius: rulersSize
        color: rulerMA3.drag.active ? Qt.lighter("steelblue", 1.2) : "steelblue"
        border.color: Qt.lighter("steelblue", 1.2)
        border.width: rulerMA3.containsMouse ? 2 : 0
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.verticalCenter: parent.top

        MouseArea {
            id: rulerMA3
            anchors.fill: parent
            hoverEnabled: true
            drag{ target: parent; axis: Drag.YAxis }
            onMouseYChanged: {
                if (drag.active) {
                    root.height = root.height - mouseY
                    if (root.height < 50) {
                        root.height = 50
                    } else {
                        root.y = root.y + mouseY
                    }

                    if (root.y < 0) {
                        root.y = 0
                        root.height = root.height + mouseY
                    }
                }
            }
        }
    }

    Rectangle {
        width: rulersSize
        height: rulersSize
        radius: rulersSize
        color: rulerMA4.drag.active ? Qt.lighter("steelblue", 1.2) : "steelblue"
        border.color: Qt.lighter("steelblue", 1.2)
        border.width: rulerMA4.containsMouse ? 2 : 0
        anchors.horizontalCenter: parent.right
        anchors.verticalCenter: parent.top

        MouseArea {
            id: rulerMA4
            anchors.fill: parent
            hoverEnabled: true
            drag{ target: parent; axis: Drag.XAndYAxis }
            onMouseYChanged: {
                if (drag.active) {
                    root.width = root.width + mouseX
                    if(root.width < 50)
                        root.width = 50

                    root.height = root.height - mouseY
                    if (root.height < 50) {
                        root.height = 50
                    } else {
                        root.y = root.y + mouseY
                    }

                    if (root.x + root.width > root.parent.width) {
                        root.width = root.parent.width - root.x
                    }

                    if (root.y < 0) {
                        root.y = 0
                        root.height = root.height + mouseY
                    }
                }
            }
        }
    }

    Rectangle {
        width: rulersSize
        height: rulersSize
        radius: rulersSize
        color: rulerMA5.drag.active ? Qt.lighter("steelblue", 1.2) : "steelblue"
        border.color: Qt.lighter("steelblue", 1.2)
        border.width: rulerMA5.containsMouse ? 2 : 0
        anchors.horizontalCenter: parent.right
        anchors.verticalCenter: parent.verticalCenter

        MouseArea {
            id: rulerMA5
            anchors.fill: parent
            hoverEnabled: true
            drag{ target: parent; axis: Drag.XAxis }
            onMouseXChanged: {
                if (drag.active) {
                    root.width = root.width + mouseX
                    if (root.width < 50) {
                        root.width = 50
                    }

                    if (root.x + root.width > root.parent.width) {
                        root.width = root.parent.width - root.x
                    }
                }
            }
        }
    }

    Rectangle {
        width: rulersSize
        height: rulersSize
        radius: rulersSize
        color: rulerMA6.drag.active ? Qt.lighter("steelblue", 1.2) : "steelblue"
        border.color: Qt.lighter("steelblue", 1.2)
        border.width: rulerMA6.containsMouse ? 2 : 0
        anchors.horizontalCenter: parent.right
        anchors.verticalCenter: parent.bottom

        MouseArea {
            id: rulerMA6
            anchors.fill: parent
            hoverEnabled: true
            drag{ target: parent; axis: Drag.XAndYAxis }
            onMouseYChanged: {
                if (drag.active) {
                    root.width = root.width + mouseX
                    if (root.width < 50) {
                        root.width = 50
                    }

                    root.height = root.height + mouseY
                    if (root.height < 50) {
                        root.height = 50
                    }

                    if (root.x + root.width > root.parent.width) {
                        root.width = root.parent.width - root.x
                    }

                    if (root.y + root.height > root.parent.height) {
                        root.height = root.parent.height - root.y
                    }
                }
            }
        }
    }

    Rectangle {
        width: rulersSize
        height: rulersSize
        radius: rulersSize
        color: rulerMA7.drag.active ? Qt.lighter("steelblue", 1.2) : "steelblue"
        border.color: Qt.lighter("steelblue", 1.2)
        border.width: rulerMA7.containsMouse ? 2 : 0
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.verticalCenter: parent.bottom

        MouseArea {
            id: rulerMA7
            anchors.fill: parent
            hoverEnabled: true
            drag{ target: parent; axis: Drag.YAxis }
            onMouseYChanged: {
                if (drag.active) {
                    root.height = root.height + mouseY
                    if (root.height < 50) {
                        root.height = 50
                    }

                    if (root.y + root.height > root.parent.height) {
                        root.height = root.parent.height - root.y
                    }
                }
            }
        }
    }

    Rectangle {
        width: rulersSize
        height: rulersSize
        radius: rulersSize
        color: rulerMA8.drag.active ? Qt.lighter("steelblue", 1.2) : "steelblue"
        border.color: Qt.lighter("steelblue", 1.2)
        border.width: rulerMA8.containsMouse ? 2 : 0
        anchors.horizontalCenter: parent.left
        anchors.verticalCenter: parent.bottom

        MouseArea {
            id: rulerMA8
            anchors.fill: parent
            hoverEnabled: true
            drag{ target: parent; axis: Drag.XAndYAxis }
            onMouseYChanged: {
                if (drag.active) {
                    root.width = root.width - mouseX
                    if (root.width < 50) {
                        root.width = 50
                    } else {
                        root.x = root.x + mouseX
                    }

                    root.height = root.height + mouseY
                    if (root.height < 50) {
                        root.height = 50
                    }

                    if (root.x < 0) {
                        root.x = 0
                        root.width = root.width + mouseX
                    }

                    if (root.y + root.height > root.parent.height) {
                        root.height = root.parent.height - root.y
                    }
                }
            }
        }
    }
}


