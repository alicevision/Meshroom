import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Controls 1.0
import MaterialIcons 2.2
import Utils 1.0

/**
 * FeaturesInfoOverlay is an overlay that displays info and
 * provides controls over a FeaturesViewer component.
 */

FloatingPane {
    id: root

    property int pluginStatus: Loader.Null
    property Item featuresViewer: null
    property var mfeatures: null
    property var mtracks: null
    property var msfmdata: null

    ColumnLayout {
        // Header
        RowLayout {
            // Node used to read features
            Label {
                text: _reconstruction && _reconstruction.activeNodes.get("featureProvider").node ? _reconstruction.activeNodes.get("featureProvider").node.label : ""
                Layout.fillWidth: true
            }
            // Settings menu
            Loader {
                active: root.pluginStatus === Loader.Ready
                sourceComponent: MaterialToolButton {
                    text: MaterialIcons.settings
                    font.pointSize: 10
                    onClicked: settingsMenu.popup(width, 0)
                    Menu {
                        id: settingsMenu
                        padding: 4
                        implicitWidth: 350

                        RowLayout {
                            Label {
                                text: "Feature Scale Filter:"
                            }
                            RangeSlider {
                                id: featureScaleFilterRS
                                ToolTip.text: "Filters features according to their scale (or filters tracks according to their average feature scale)."
                                ToolTip.visible: hovered
                                Layout.fillHeight: true
                                Layout.alignment: Qt.AlignRight
                                from: 0
                                to: 1
                                first.value: 0
                                first.onMoved: { root.featuresViewer.featureMinScaleFilter = Math.pow(first.value,4) }
                                second.value: 1
                                second.onMoved: { root.featuresViewer.featureMaxScaleFilter = Math.pow(second.value,4) }
                                stepSize: 0.01
                            }
                        }
                        RowLayout {
                            Label {
                                text: "Feature Display Mode:"
                            }
                            ComboBox {
                                id: featureDisplayModeCB
                                flat: true
                                ToolTip.text: "Feature Display Mode:\n" +
                                              "* Points: Simple points.\n" +
                                              "* Square: Scaled filled squares.\n" +
                                              "* Oriented Square: Scaled and oriented squares."
                                ToolTip.visible: hovered
                                Layout.fillHeight: true
                                Layout.alignment: Qt.AlignRight
                                model: root.featuresViewer ? root.featuresViewer.featureDisplayModes : null
                                currentIndex: root.featuresViewer ? root.featuresViewer.featureDisplayMode : 0
                                onActivated: root.featuresViewer.featureDisplayMode = currentIndex
                            }
                        }
                        RowLayout {
                            Label {
                                text: "Track Display Mode:"
                            }
                            ComboBox {
                                id: trackDisplayModeCB
                                flat: true
                                ToolTip.text: "Track Display Mode:\n" +
                                              "* Lines Only: Only track lines.\n" +
                                              "* Current Matches: Track lines with current matches/landmarks.\n" +
                                              "* All Matches: Track lines with all matches / landmarks."
                                ToolTip.visible: hovered
                                Layout.fillHeight: true
                                Layout.alignment: Qt.AlignRight
                                model: root.featuresViewer ? root.featuresViewer.trackDisplayModes : null
                                currentIndex: root.featuresViewer ? root.featuresViewer.trackDisplayMode : 0
                                onActivated: root.featuresViewer.trackDisplayMode = currentIndex
                            }
                        }
                        RowLayout {
                            Label {
                                text: "Track Contiguous Filter:"
                            }
                            CheckBox {
                                id: trackContiguousFilterCB
                                ToolTip.text: "Hides non-contiguous track parts."
                                ToolTip.visible: hovered
                                Layout.fillHeight: true
                                Layout.alignment: Qt.AlignRight
                                checked: root.featuresViewer ? root.featuresViewer.trackContiguousFilter : false
                                onClicked: root.featuresViewer.trackContiguousFilter = trackContiguousFilterCB.checked
                            }
                        }
                        RowLayout {
                            Label {
                                text: "Track Inliers Filter:"
                            }
                            CheckBox {
                                id: trackInliersFilterCB
                                ToolTip.text: "Hides tracks without at least one inlier."
                                ToolTip.visible: hovered
                                Layout.fillHeight: true
                                Layout.alignment: Qt.AlignRight
                                checked: root.featuresViewer ? root.featuresViewer.trackInliersFilter : false
                                onClicked: root.featuresViewer.trackInliersFilter = trackInliersFilterCB.checked
                            }
                        }
                        RowLayout {
                            Label {
                                text: "Display 3D Tracks:"
                            }
                            CheckBox {
                                id: display3dTracksCB
                                ToolTip.text: "Draws tracks between 3d points instead of 2d points (if possible)."
                                ToolTip.visible: hovered
                                Layout.fillHeight: true
                                Layout.alignment: Qt.AlignRight
                                checked: root.featuresViewer ? root.featuresViewer.display3dTracks : false
                                onClicked: root.featuresViewer.display3dTracks = display3dTracksCB.checked
                            }
                        }
                        RowLayout {
                            Label {
                                text: "Display Track Endpoints:"
                            }
                            CheckBox {
                                id: displayTrackEndpointsCB
                                ToolTip.text: "Draws markers indicating the global start/end point of each track."
                                ToolTip.visible: hovered
                                Layout.fillHeight: true
                                Layout.alignment: Qt.AlignRight
                                checked: root.featuresViewer ? root.featuresViewer.displayTrackEndpoints : false
                                onClicked: root.featuresViewer.displayTrackEndpoints = displayTrackEndpointsCB.checked
                            }
                        }
                        RowLayout {
                            Label {
                                text: "Time Window:"
                            }
                            SpinBox {
                                id: timeWindowSB
                                ToolTip.text: "Time Window: The number of frames to consider for tracks display.\n" +
                                              "e.g. With time window set at x, tracks will start at current frame - x and they will end at  current frame + x."
                                ToolTip.visible: hovered
                                Layout.fillHeight: true
                                Layout.alignment: Qt.AlignRight
                                from: -1
                                to: 50
                                value: root.featuresViewer ? root.featuresViewer.timeWindow : 0
                                stepSize: 1
                                editable: true

                                textFromValue: function(value, locale) {
                                    if (value === -1) return "No Limit"
                                    if (value ===  0) return "Disable"
                                    return value
                                }

                                valueFromText: function(text, locale) {
                                    if (text === "No Limit") return -1
                                    if (text === "Disable")  return 0
                                    return Number.fromLocaleString(locale, text)
                                }

                                onValueChanged: {
                                    if (root.featuresViewer)
                                        root.featuresViewer.timeWindow = timeWindowSB.value
                                }
                            }
                        }
                    }
                }
            }
        }

        // Error message if AliceVision plugin is unavailable
        Label {
            visible: root.pluginStatus === Loader.Error
            text: "AliceVision plugin is required to display features"
            color: Colors.red
        }

        // Feature types
        ListView {
            implicitHeight: contentHeight
            implicitWidth: contentItem.childrenRect.width

            model: root.featuresViewer !== null ? root.featuresViewer.model : 0

            delegate: RowLayout {
                id: featureType
                property var viewer: root.featuresViewer.itemAt(index)
                spacing: 4

                // Features visibility toggle
                MaterialToolButton {
                    id: featuresVisibilityButton
                    checkable: true
                    checked: true
                    text: MaterialIcons.center_focus_strong
                    ToolTip.text: "Display Extracted Features"
                    onClicked: {
                        featureType.viewer.displayFeatures = featuresVisibilityButton.checked
                    }
                    font.pointSize: 10
                    opacity: featureType.viewer.visible ? 1.0 : 0.6
                }
                // Tracks visibility toggle
                MaterialToolButton {
                    id: tracksVisibilityButton
                    checkable: true
                    checked: false
                    text: MaterialIcons.timeline
                    ToolTip.text: "Display Tracks"
                    onClicked: {
                        featureType.viewer.displayTracks = tracksVisibilityButton.checked
                        root.featuresViewer.enableTimeWindow = tracksVisibilityButton.checked
                    }
                    font.pointSize: 10
                }
                // Matches visibility toggle
                MaterialToolButton {
                    id: matchesVisibilityButton
                    checkable: true
                    checked: true
                    text: MaterialIcons.sync
                    ToolTip.text: "Display Matches"
                    onClicked: {
                        featureType.viewer.displayMatches = matchesVisibilityButton.checked
                    }
                    font.pointSize: 10
                }
                // Landmarks visibility toggle
                MaterialToolButton {
                    id: landmarksVisibilityButton
                    checkable: true
                    checked: true
                    text: MaterialIcons.fiber_manual_record
                    ToolTip.text: "Display Landmarks"
                    onClicked: {
                        featureType.viewer.displayLandmarks = landmarksVisibilityButton.checked
                    }
                    font.pointSize: 10
                }
                // ColorChart picker
                ColorChart {
                    implicitWidth: 12
                    implicitHeight: implicitWidth
                    colors: root.featuresViewer.colors
                    currentIndex: featureType.viewer.colorIndex
                    // offset featuresViewer color set when changing the color of one feature type
                    onColorPicked: function(colorIndex) {
                        featureType.viewer.colorOffset = colorIndex - index
                    }
                }
                // Feature type name
                Label {
                    property string descType: featureType.viewer.describerType
                    property int viewId: root.featuresViewer.currentViewId
                    text: descType + ": " + ((root.mfeatures && root.mfeatures.status === MFeatures.Ready) ? root.mfeatures.nbFeatures(descType, viewId) : " - ") + " / " + ((root.mtracks && root.mtracks.status === MTracks.Ready) ? root.mtracks.nbMatches(descType, viewId) : " - ") + " / " + ((root.msfmdata && root.msfmdata.status === MSfMData.Ready) ? root.msfmdata.nbLandmarks(descType, viewId) : " - ")
                }
                // Feature loading status
                Loader {
                    active: (root.mfeatures && root.mfeatures.status === MFeatures.Loading)
                    sourceComponent: BusyIndicator {
                        padding: 0
                        implicitWidth: 12
                        implicitHeight: 12
                        running: true
                    }
                }
            }
        }
    }
}
