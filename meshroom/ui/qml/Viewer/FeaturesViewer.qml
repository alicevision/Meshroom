import QtQuick

import AliceVision 1.0 as AliceVision
import Utils 1.0

/**
 * FeaturesViewer displays the extracted feature points of a View.
 * Requires QtAliceVision plugin.
 */

Repeater {
    id: root

    /// Features
    property var features
    /// Tracks
    property var tracks
    /// SfMData
    property var sfmData

    /// The list of describer types to load
    property alias describerTypes: root.model

    /// List of available feature display modes
    readonly property var featureDisplayModes: ['Points', 'Squares', 'Oriented Squares']
    /// Current feature display mode index
    property int featureDisplayMode: 2

    /// List of available track display modes
    readonly property var trackDisplayModes: ['Lines Only', 'Current Matches', 'All Matches']
    /// Current track display mode index
    property int trackDisplayMode: 1

    // Minimum feature scale score to display
    property real featureMinScaleFilter: 0
    // Maximum feature scale score to display
    property real featureMaxScaleFilter: 1

    /// Display 3d tracks
    property bool display3dTracks: false

    /// Display only contiguous tracks
    property bool trackContiguousFilter: true

    /// Display only tracks with at least one inlier
    property bool trackInliersFilter: false

    /// Display track endpoints
    property bool displayTrackEndpoints: true

    /// The list of colors used for displaying several describers
    property var colors: [Colors.blue, Colors.green, Colors.yellow, Colors.cyan, Colors.pink, Colors.lime] //, Colors.orange, Colors.red

    /// Current view ID
    property var currentViewId
    property bool syncFeaturesSelected: false

    /// Time window
    property bool enableTimeWindow: false
    property int timeWindow: 1

    model: root.describerTypes

    // Instantiate one FeaturesViewer by describer type
    delegate: AliceVision.FeaturesViewer {
        readonly property int colorIndex: (index + colorOffset) % root.colors.length
        property int colorOffset: 0
        featureDisplayMode: root.featureDisplayMode
        trackDisplayMode: root.trackDisplayMode
        featureMinScaleFilter: root.featureMinScaleFilter
        featureMaxScaleFilter: root.featureMaxScaleFilter
        display3dTracks: root.display3dTracks
        trackContiguousFilter: root.trackContiguousFilter
        trackInliersFilter: root.trackInliersFilter
        displayTrackEndpoints: root.displayTrackEndpoints
        featureColor: root.colors[colorIndex]
        matchColor: Colors.orange
        landmarkColor: Colors.red
        describerType: modelData
        currentViewId: syncFeaturesSelected ? _reconstruction.pickedViewId : root.currentViewId
        enableTimeWindow: root.enableTimeWindow
        timeWindow: root.timeWindow
        mfeatures: root.features
        mtracks: root.tracks
        msfmData: root.sfmData
    }
}
