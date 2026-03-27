import QtQuick
import QtQuick.Controls

import Utils 1.0

/**
 * A Slider styled as a timeline: a ruler with tick marks and frame number
 * labels sits above a track that highlights cached frame intervals in blue.
 * The handle is a "playhead" — a downward-pointing triangle connected to a
 * thin vertical line — rather than the default circular thumb.
 */
Slider {
    id: root

    // Array of {x: startFrameIndex, y: endFrameIndex} intervals
    property var cachedFrames: []

    readonly property int _trackHeight: 8
    readonly property int _rulerHeight: 20

    implicitHeight: _rulerHeight + _trackHeight + topPadding + bottomPadding

    // ── Playhead handle ──────────────────────────────────────────────────────
    handle: Item {
        // Center the playhead on the logical slider position
        x: root.leftPadding + root.visualPosition * root.availableWidth - width / 2
        y: root.topPadding
        width: 10
        height: root.availableHeight

        // Downward-pointing triangle marker
        Canvas {
            id: playheadMarker

            anchors.top: parent.top
            anchors.horizontalCenter: parent.horizontalCenter
            width: parent.width
            height: 7

            property color markerColor: root.palette.highlight

            onMarkerColorChanged: requestPaint()
            Component.onCompleted: requestPaint()

            onPaint: {
                var ctx = getContext("2d")
                ctx.reset()
                ctx.fillStyle = markerColor.toString()
                ctx.beginPath()
                ctx.moveTo(0, 0)
                ctx.lineTo(width, 0)
                ctx.lineTo(width / 2, height)
                ctx.closePath()
                ctx.fill()
            }
        }

        // Vertical playhead line below the triangle
        Rectangle {
            anchors.top: playheadMarker.bottom
            anchors.bottom: parent.bottom
            anchors.horizontalCenter: parent.horizontalCenter
            width: 2
            color: root.palette.highlight
            opacity: 0.9
        }
    }

    // ── Background: ruler + track ────────────────────────────────────────────
    background: Item {
        x: root.leftPadding
        y: root.topPadding
        width: root.availableWidth
        height: root.availableHeight

        // Ruler: tick marks and frame-number labels
        Item {
            id: ruler

            anchors.top: parent.top
            width: parent.width
            height: root._rulerHeight

            readonly property int range: root.to - root.from

            // Pick a "nice" interval so there are roughly 10-15 major ticks
            readonly property int majorInterval: {
                if (range <= 0)   return 1
                if (range <= 10)  return 1
                if (range <= 25)  return 5
                if (range <= 50)  return 10
                if (range <= 250) return 50
                if (range <= 500) return 100
                return 250
            }

            Repeater {
                model: ruler.range > 0 ? Math.floor(ruler.range / ruler.majorInterval) + 1 : 1

                Item {
                    readonly property int frameNum: root.from + index * ruler.majorInterval
                    readonly property real xPos: ruler.range > 0
                        ? (frameNum - root.from) / ruler.range * ruler.width
                        : 0

                    x: xPos - width / 2
                    width: Math.max(1, frameLabel.implicitWidth)
                    height: ruler.height

                    Text {
                        id: frameLabel
                        anchors.top: parent.top
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: frameNum
                        font.pixelSize: 9
                        color: Colors.lightgrey
                    }

                    Rectangle {
                        anchors.bottom: parent.bottom
                        anchors.horizontalCenter: parent.horizontalCenter
                        width: 1
                        height: 5
                        color: Colors.lightgrey
                    }
                }
            }
        }

        // Track: grey base with blue cached-frame segments
        Rectangle {
            id: track

            anchors.bottom: parent.bottom
            width: parent.width
            height: root._trackHeight
            radius: height / 2
            color: Colors.grey

            Repeater {
                id: cacheView

                model: root.cachedFrames
                property real frameLength: (root.to - root.from + 1) > 0
                    ? track.width / (root.to - root.from + 1)
                    : 0

                Rectangle {
                    x: modelData.x * cacheView.frameLength
                    y: 0
                    width: cacheView.frameLength * (modelData.y - modelData.x + 1)
                    height: track.height
                    radius: track.radius
                    color: Colors.blue
                }
            }
        }
    }
}
