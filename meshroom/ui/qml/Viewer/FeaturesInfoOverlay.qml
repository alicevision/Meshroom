import QtQuick 2.9
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3
import MaterialIcons 2.2

import Utils 1.0
import Controls 1.0

/**
 * FeaturesInfoOverlay is an overlay that displays info and
 * provides controls over a FeaturesViewer component.
 */
FloatingPane {
    id: root

    property int pluginStatus: Loader.Null
    property Item featuresViewer: null
    property var mfeatures: null
    property var featureExtractionNode: null

    ColumnLayout {
        // Header
        RowLayout {
            // FeatureExtraction node name
            Label {
                text: featureExtractionNode ? featureExtractionNode.label : ""
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
                                text: "Feature Display Mode:"
                            }
                            ComboBox {
                                id: featureDisplayModeCB
                                flat: true
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
                                Layout.fillHeight: true
                                Layout.alignment: Qt.AlignRight
                                checked: root.featuresViewer.trackContiguousFilter
                                onClicked: root.featuresViewer.trackContiguousFilter = trackContiguousFilterCB.checked
                            }
                        }
                        RowLayout {
                            Label {
                                text: "Track Inliers Filter:"
                            }
                            CheckBox {
                                id: trackInliersFilterCB
                                Layout.fillHeight: true
                                Layout.alignment: Qt.AlignRight
                                checked: root.featuresViewer.trackInliersFilter
                                onClicked: root.featuresViewer.trackInliersFilter = trackInliersFilterCB.checked
                            }
                        }
                        RowLayout {
                            Label {
                                text: "Track Feature Scale Filter:"
                            }
                            RangeSlider {
                                id: trackFeatureScaleFilterRS
                                Layout.fillHeight: true
                                Layout.alignment: Qt.AlignRight
                                from: 0
                                to: 1
                                first.value: root.featuresViewer.trackMinFeatureScaleFilter
                                first.onMoved: { root.featuresViewer.trackMinFeatureScaleFilter = first.value; }
                                second.value: root.featuresViewer.trackMaxFeatureScaleFilter
                                second.onMoved: { root.featuresViewer.trackMaxFeatureScaleFilter = second.value; }
                                stepSize: 0.01
                            }
                        }
                        RowLayout {
                            Label {
                                text: "Time Window:"
                            }
                            SpinBox {
                                id: timeWindowSB
                                Layout.fillHeight: true
                                Layout.alignment: Qt.AlignRight
                                from: -1
                                to: 50
                                value: root.mfeatures.timeWindow
                                stepSize: 1

                                textFromValue: function(value) {
                                    if (value == -1) return "No Limit";
                                    if (value ==  0) return "Disable";
                                    return value;
                                }

                                valueFromText: function(text) {
                                    if (value == "No Limit") return -1;
                                    if (value == "Disable")  return 0;
                                    return value;
                                }

                                onValueChanged: {
                                    root.mfeatures.timeWindow = timeWindowSB.value;
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
                    onClicked: {
                        featureType.viewer.displayFeatures = featuresVisibilityButton.checked;
                    }
                    font.pointSize: 10
                    opacity: featureType.viewer.visible ? 1.0 : 0.6
                }
                // Tracks visibility toogle
                MaterialToolButton {
                    id: tracksVisibilityButton
                    checkable: true
                    checked: false
                    text: MaterialIcons.timeline
                    onClicked: {
                        featureType.viewer.displayTracks = tracksVisibilityButton.checked;
                        root.mfeatures.enableTimeWindow = tracksVisibilityButton.checked;
                    }
                    font.pointSize: 10
                }
                // Matches visibility toogle
                MaterialToolButton {
                    id: matchesVisibilityButton
                    checkable: true
                    checked: true
                    text: MaterialIcons.sync
                    onClicked: {
                        featureType.viewer.displayMatches = matchesVisibilityButton.checked;
                    }
                    font.pointSize: 10
                }
                // Landmarks visibility toogle
                MaterialToolButton {
                    id: landmarksVisibilityButton
                    checkable: true
                    checked: true
                    text: MaterialIcons.fiber_manual_record
                    onClicked: {
                        featureType.viewer.displayLandmarks = landmarksVisibilityButton.checked;
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
                    onColorPicked: featureType.viewer.colorOffset = colorIndex - index
                }
                // Feature type name
                Label {
                    text: {
                        if(featureType.viewer.loadingFeatures)
                            return  featureType.viewer.describerType;
                        return featureType.viewer.describerType + ": " +
                                ((featureExtractionNode && featureExtractionNode.isComputed) ? root.mfeatures.featuresInfo[featureType.viewer.describerType][root.mfeatures.currentViewId]['nbFeatures'] : " - ") + " / " +
                                (root.mfeatures.haveValidTracks ? root.mfeatures.featuresInfo[featureType.viewer.describerType][root.mfeatures.currentViewId]['nbTracks']  : " - ") + " / " +
                                (root.mfeatures.haveValidLandmarks ? root.mfeatures.featuresInfo[featureType.viewer.describerType][root.mfeatures.currentViewId]['nbLandmarks'] : " - ");
                    }
                }
                // Feature loading status
                Loader {
                    active: (root.mfeatures.status === MFeatures.Loading)
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