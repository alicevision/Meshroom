import QtQuick 2.15
import AliceVision 1.0 as AliceVision

import Utils 1.0

/**
 * FeaturesViewer displays the extracted feature points of a View.
 * Requires QtAliceVision plugin.
 */
Repeater {
    id: root

    /// ViewID to display the features of a specific view
    property int viewId
    /// SfMData to display the data of SfM
    property var sfmData
    /// Folder containing the features files
    property string featureFolder
    /// Tracks object loading all the matches files
    property var tracks
    /// The list of describer types to load
    property alias describerTypes: root.model
    /// List of available display modes
    readonly property var displayModes: ['Points', 'Squares', 'Oriented Squares']
    /// Current display mode index
    property int displayMode: 2
    /// The list of colors used for displaying several describers
    property var colors: [Colors.blue, Colors.green, Colors.yellow, Colors.orange, Colors.cyan, Colors.pink, Colors.lime] //, Colors.red

    model: root.describerTypes

    // instantiate one FeaturesViewer by describer type
    delegate: AliceVision.FeaturesViewer {
        readonly property int colorIndex: (index + colorOffset) % root.colors.length
        property int colorOffset: 0
        describerType: modelData
        featureFolder: root.featureFolder
        mtracks: root.tracks
        viewId: root.viewId
        color: root.colors[colorIndex]
        landmarkColor: Colors.red
        displayMode: root.displayMode
        msfmData: root.sfmData
    }

}
