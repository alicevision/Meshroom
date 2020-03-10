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
    property var featureExtractionNode: null

    ColumnLayout {

        // Header
        RowLayout {
            // FeatureExtraction node name
            Label {
                text: featureExtractionNode.label
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
                        implicitWidth: 210

                        RowLayout {
                            Label {
                                text: "Display Mode:"
                            }
                            ComboBox {
                                id: displayModeCB
                                flat: true
                                Layout.fillWidth: true
                                model: root.featuresViewer.displayModes
                                onActivated: root.featuresViewer.displayMode = currentIndex
                            }
                        }
                    }
                }
            }
        }

        // Error message if AliceVision plugin is unavailable
        Label {
            visible: root.pluginStatus === Loader.Error
            text: "AliceVision plugin is required to display Features"
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

                // Visibility toogle
                MaterialToolButton {
                    text: featureType.viewer.visible ? MaterialIcons.visibility : MaterialIcons.visibility_off
                    onClicked: featureType.viewer.visible = !featureType.viewer.visible
                    font.pointSize: 10
                    opacity: featureType.viewer.visible ? 1.0 : 0.6
                }
                // ColorChart picker
                ColorChart {
                    implicitWidth: 12
                    implicitHeight: implicitWidth
                    colors: root.featuresViewer.colors
                    currentIndex: featureType.viewer.colorIndex
                    // offset featuresViewer color set when changing the color of one feature type
                    onColorPicked: root.featuresViewer.colorOffset = colorIndex - index
                }
                // Feature type name
                Label {
                    text: featureType.viewer.describerType + (featureType.viewer.loading ? "" : ": " + featureType.viewer.features.length)
                }
                // Feature loading status
                Loader {
                    active: featureType.viewer.loading
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
