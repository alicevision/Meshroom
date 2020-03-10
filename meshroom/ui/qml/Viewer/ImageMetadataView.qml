import QtQuick 2.9
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3
import MaterialIcons 2.2
import QtPositioning 5.8
import QtLocation 5.9

import Controls 1.0
import Utils 1.0

/**
 * ImageMetadataView displays a JSON model representing an image"s metadata as a ListView.
 */
FloatingPane {
    id: root

    property alias metadata: metadataModel.metadata
    property var coordinates: QtPositioning.coordinate()

    clip: true
    padding: 4

    /**
     * Convert GPS metadata to degree coordinates.
     *
     * GPS coordinates in metadata can be store in 3 forms:
     * (degrees), (degrees, minutes), (degrees, minutes, seconds)
     */
    function gpsMetadataToCoordinates(value, ref)
    {
        var values = value.split(",")
        var result = 0
        for(var i=0; i < values.length; ++i)
        {
            // divide each component by the corresponding power of 60
            // 1 for degree, 60 for minutes, 3600 for seconds
            result += Number(values[i]) / Math.pow(60, i)
        }
        // handle opposite reference: South (latitude) or West (longitude)
        return (ref === "S" || ref === "W") ? -result : result
    }

    /// Try to get GPS coordinates from metadata
    function getGPSCoordinates(metadata)
    {
        // GPS data available
        if(metadata && metadata["GPS:Longitude"] != undefined && metadata["GPS:Latitude"] != undefined)
        {
            var latitude = gpsMetadataToCoordinates(metadata["GPS:Latitude"], metadata["GPS:LatitudeRef"])
            var longitude = gpsMetadataToCoordinates(metadata["GPS:Longitude"], metadata["GPS:LongitudeRef"])
            var altitude = metadata["GPS:Altitude"] || 0
            return QtPositioning.coordinate(latitude, longitude, altitude)
        }
        // GPS data unavailable: reset coordinates to default value
        else
        {
            return QtPositioning.coordinate()
        }
    }

    // Metadata model
    // Available roles for child items:
    //   - group: metadata group if any, "-" otherwise
    //   - key: metadata key
    //   - value: metadata value
    //   - raw: a sortable/filterable representation of the metadata as "group:key=value"
    ListModel {
        id: metadataModel
        property var metadata: ({})

        // reset model when metadata changes
        onMetadataChanged: {
            metadataModel.clear()
            var entries = []
            // prepare data to populate the model from the input metadata object
            for(var key in metadata)
            {
                var entry = {}
                entry["raw"] = key
                // split on ":" to get group and key
                var sKey = key.split(":", 2)
                if(sKey.length === 2)
                {
                    entry["group"] = sKey[0]
                    entry["key"] = sKey[1]
                }
                else
                {
                    // set default group to something convenient for sorting
                    entry["group"] = "-"
                    entry["key"] = key
                }
                entry["value"] = metadata[key]
                entry["raw"] = entry["group"] + ":" + entry["key"] + "=" + entry["value"]
                entries.push(entry)
            }
            // reset the model with prepared data (limit to one update event)
            metadataModel.append(entries)
            coordinates = getGPSCoordinates(metadata)
        }
    }

//    Button {
//        onClicked: {
//            if(sortedMetadataModel.sortOrder == Qt.DescendingOrder)
//                sortedMetadataModel.sortOrder = Qt.AscendingOrder
//            else
//                sortedMetadataModel.sortOrder = Qt.DescendingOrder
//        }
//    }

    // Background WheelEvent grabber
    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.MiddleButton
        onWheel: wheel.accepted = true
    }


    // Main Layout
    ColumnLayout {
        anchors.fill: parent

        SearchBar {
            id: searchBar
            Layout.fillWidth: true
        }

        // Metadata ListView
        ListView {
            id: metadataView
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 3
            clip: true

            // SortFilter delegate over the metadataModel
            model: SortFilterDelegateModel {
                id: sortedMetadataModel
                model: metadataModel
                sortRole: "raw"
                filterRole: "raw"
                filterValue: searchBar.text
                delegate: RowLayout {
                    width: parent.width
                    Label {
                        text: key
                        leftPadding: 6
                        rightPadding: 4
                        Layout.preferredWidth: sizeHandle.x
                        elide: Text.ElideRight
                    }
                    Label {
                        text: value
                        Layout.fillWidth: true
                        wrapMode: Label.WrapAtWordBoundaryOrAnywhere
                    }
                }
            }

            // Categories resize handle
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
                        minimumX: metadataView.width * 0.2
                        maximumX: metadataView.width * 0.8
                    }
                }
            }
            // Display section based on metadata group
            section.property: "group"
            section.delegate: Pane {
                width: parent.width
                padding: 3
                background: null

                Label {
                    width: parent.width
                    padding: 2
                    background: Rectangle { color: parent.palette.mid }
                    text: section
                }
            }
            ScrollBar.vertical: ScrollBar{}
        }


        // Display map if GPS coordinates are available
        Loader {
            Layout.fillWidth: true
            Layout.preferredHeight: coordinates.isValid ? 160 : 0

            active: coordinates.isValid

            Plugin {
                id: osmPlugin
                name: "osm"
            }

            sourceComponent: Map {
                id: map
                plugin: osmPlugin
                center: coordinates

                function recenter() {
                    center = coordinates
                }

                Connections {
                    target: root
                    onCoordinatesChanged: recenter()
                }

                zoomLevel: 16
                // Coordinates visual indicator
                MapQuickItem {
                    coordinate: coordinates
                    anchorPoint.x: circle.paintedWidth / 2
                    anchorPoint.y: circle.paintedHeight
                    sourceItem: Text {
                        id: circle
                        color: root.palette.highlight
                        font.pointSize: 18
                        font.family: MaterialIcons.fontFamily
                        text: MaterialIcons.location_on
                    }
                }
                // Reset map center
                FloatingPane {
                    anchors.right: parent.right
                    anchors.top: parent.top
                    padding: 2
                    visible: map.center != coordinates

                    ToolButton {
                        font.family: MaterialIcons.fontFamily
                        text: MaterialIcons.my_location
                        ToolTip.visible: hovered
                        ToolTip.text: "Recenter"
                        padding: 0
                        onClicked: recenter()
                    }
                }
            }
        }
    }
}
