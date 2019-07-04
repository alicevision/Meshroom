import QtQuick 2.11
import AliceVision 1.0 as AliceVision

import Utils 1.0

/**
 * FeaturesViewer displays the extracted feature points of a View.
 * Requires QtAliceVision plugin.
 */
Repeater {
    id: root

    /// ViewID to display the features of
    property int viewId
    /// Folder containing the features files
    property string folder
    /// The list of describer types to load
    property alias describerTypes: root.model
    /// List of available display modes
    readonly property var displayModes: ['Points', 'Squares', 'Oriented Squares']
    /// Current display mode index
    property int displayMode: 0
    /// The list of colors used for displaying several describers
    property var colors: [Colors.blue, Colors.red, Colors.yellow, Colors.green, Colors.orange, Colors.cyan, Colors.pink, Colors.lime]
    /// Offset the color list
    property int colorOffset: 0

    model: root.describerTypes

    // instantiate one FeaturesViewer by describer type
    delegate: AliceVision.FeaturesViewer {
        readonly property int colorIndex: (index+root.colorOffset)%root.colors.length
        describerType: modelData
        folder: root.folder
        viewId: root.viewId
        color: root.colors[colorIndex]
        displayMode: root.displayMode
    }

}
