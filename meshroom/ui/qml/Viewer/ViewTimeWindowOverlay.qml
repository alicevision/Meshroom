import QtQuick 2.9
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3
import MaterialIcons 2.2

import Utils 1.0
import Controls 1.0

/**
 * ViewTimeWindowOverlay is an overlay that displays view information provided by the MFeatures object.
 */
FloatingPane {
    id: root

    property var mfeatures: null

    clip: true
    padding: 4
    anchors.rightMargin: 0

    ListModel {
        id: viewModel
        property var featuresInfo: root.mfeatures.featuresInfo

        onFeaturesInfoChanged: {
            viewModel.clear()
            var entries = []

            // prepare data to populate the model from the input featuresInfo object
            for(var describerType in featuresInfo)
            {
                for(var viewId in featuresInfo[describerType])
                {
                    var entry = featuresInfo[describerType][viewId]; // see QtAliceVision for featuresInfo list of attributes
                    entry["key"] = viewId;
                    entries.push(entry)
                }
            }
            viewModel.append(entries)
        }
    }

    // background WheelEvent grabber
    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.MiddleButton
        onWheel: wheel.accepted = true
    }

    // main Layout
    ColumnLayout {
        anchors.fill: parent

        // listView
        ListView {
            id: listView
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 3
            clip: true

            model: viewModel
            delegate: RowLayout {
                width: parent.width
                Label {
                    text: key
                    leftPadding: 6
                    rightPadding: 4
                    Layout.preferredWidth: sizeHandle.x
                    elide: Text.ElideRight
                }
                ColumnLayout{
                    RowLayout {
                        Label {text: 'frameId: '}
                        Label {text: frameId }
                    }
                    RowLayout {
                        Label {text: 'nbFeatures: '}
                        Label {text: nbFeatures }
                    }
                    RowLayout {
                        Label {text: 'nbTracks: '}
                        Label {text: nbTracks }
                    }
                    RowLayout {
                        Label {text: 'nbLandmarks: '}
                        Label {text: nbLandmarks }
                    }
                }
            }

            // resize handle
            Rectangle {
                id: sizeHandle
                height: parent.contentHeight
                width: 1
                color: root.palette.mid
                x: parent.width * 0.4
                MouseArea {
                    anchors.fill: parent
                    anchors.margins: -4
                    cursorShape: Qt.SizeHorCursor
                    drag {
                        target: parent
                        axis: Drag.XAxis
                        threshold: 0
                        minimumX: listView.width * 0.2
                        maximumX: listView.width * 0.8
                    }
                }
            }

            ScrollBar.vertical: ScrollBar{}
        }
    }
}