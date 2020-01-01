import QtQuick 2.9


/**
 * Canvas that can be painted on using the mouse.
 */
Canvas {
    id: root
    anchors.fill: parent

    property int lineWidth: 15
    property int xpos
    property int ypos
    property int lastxpos: -1
    property int lastypos: -1
    property bool stroke

    function clear() {
        var ctx = getContext("2d")
        ctx.reset()
        requestPaint()
    }

    onPaint: {
        var ctx = getContext("2d")

        ctx.lineWidth = root.lineWidth
        ctx.lineCap = "round"
        ctx.lineJoin = "round"

        if ((paintMA.pressedButtons & Qt.RightButton) && !(paintMA.pressedButtons & Qt.LeftButton)) {
            ctx.strokeStyle = "red"
        } else if ((paintMA.pressedButtons & Qt.LeftButton) && !(paintMA.pressedButtons & Qt.RightButton)) {
            ctx.strokeStyle = "blue"
        }
        
        ctx.beginPath()
        ctx.moveTo(lastxpos, lastypos)
        if (stroke) {
            ctx.lineTo(xpos, ypos)
        } else if (lastxpos != -1) {
            context.arc(xpos, ypos, 0.5, 0, 360);
        }
        ctx.stroke()

        lastxpos = xpos
        lastypos = ypos
        stroke = true
    }

    MouseArea {
        id: paintMA

        anchors.fill: parent

        acceptedButtons: Qt.LeftButton | Qt.RightButton

        onPressed: {
            root.xpos = mouseX
            root.ypos = mouseY
            root.lastxpos = mouseX
            root.lastypos = mouseY
            root.stroke = false
            root.requestPaint()
        }
        onMouseXChanged: {
            root.xpos = mouseX
            root.ypos = mouseY
            root.requestPaint()
        }
        onMouseYChanged: {
            root.xpos = mouseX
            root.ypos = mouseY
            root.requestPaint()
        }
    }
}


