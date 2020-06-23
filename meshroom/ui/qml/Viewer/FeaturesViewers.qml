import QtQuick 2.11
import AliceVision 1.0 as AliceVision

import Utils 1.0

/**
 * FeaturesViewer displays the extracted feature points of a View.
 * Requires QtAliceVision plugin.
 */

Repeater {
    id: root

    /// MFeatures instance
    property var mfeatures
    /// List of available display modes
    readonly property var displayModes: ['Points', 'Squares', 'Oriented Squares']
    /// Current display mode index
    property int displayMode: 2
    /// The list of colors used for displaying several describers
    property var colors: [Colors.blue, Colors.green, Colors.yellow, Colors.orange, Colors.cyan, Colors.pink, Colors.lime] //, Colors.red

    model: mfeatures.describerTypes

    // instantiate one FeaturesViewer by describer type
    delegate: AliceVision.FeaturesViewer {
        readonly property int colorIndex: (index + colorOffset) % root.colors.length
        property int colorOffset: 0
        describerType: modelData
        color: root.colors[colorIndex]
        landmarkColor: Colors.red
        displayMode: root.displayMode
        mdescFeatures: root.mfeatures.allFeatures.hasOwnProperty(modelData) ? root.mfeatures.allFeatures[modelData] : null
    }
}