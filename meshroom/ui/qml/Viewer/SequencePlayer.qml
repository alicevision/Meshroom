import QtCore
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Controls 1.0
import MaterialIcons 2.2
import Utils 1.0

/**
 * The Sequence Player is a UI for manipulating
 * the currently selected (and displayed) viewpoint
 * in an ordered set of viewpoints (i.e. a sequence).
 *
 * The viewpoint manipulation process can be manual
 * (for example by dragging a slider to change the current frame)
 * or automatic
 * (by playing the sequence, i.e. incrementing the current frame at a given time rate).
 */
FloatingPane {
    id: root

    // Exposed properties
    property var sortedViewIds: []
    property var viewer: null
    property bool isOutputSequence: false
    readonly property alias sync3DSelected: m.sync3DSelected
    readonly property alias syncFeaturesSelected: m.syncFeaturesSelected
    property bool loading: fetchButton.checked || m.playing
    property alias settings_SequencePlayer: settings_SequencePlayer
    property alias frameId: m.frame
    property var frameRange: { "min" : 0, "max" : 0 }

    Settings {
        id: settings_SequencePlayer
        property int maxCacheMemory: viewer && viewer.ramInfo != undefined ? viewer.ramInfo.x / 4 : 0
    }

    function updateReconstructionView() {
        if (isOutputSequence)
            return
        if (_reconstruction && m.frame >= frameRange.min && m.frame < frameRange.max + 1) {
            if (!m.playing && !frameSlider.pressed) {
                _reconstruction.selectedViewId = sortedViewIds[m.frame]
            } else {
                _reconstruction.pickedViewId = sortedViewIds[m.frame]
                if (m.sync3DSelected) {
                    _reconstruction.updateSelectedViewpoint(_reconstruction.pickedViewId)
                }
            }
        }
    }

    onIsOutputSequenceChanged: {
        if (!isOutputSequence) {
            frameId = frameRange.min
        }
    }

    onSortedViewIdsChanged: {
        frameSlider.from = frameRange.min
        frameSlider.to = frameRange.max
    }

    // Sequence player model:
    // - current frame
    // - data related to automatic sequence playing
    QtObject {
        id: m

        property int frame: frameRange.min
        property bool syncFeaturesSelected: true
        property bool sync3DSelected: true
        property bool playing: false
        property bool repeat: false
        property real fps: 24

        onFrameChanged: {
            updateReconstructionView()
        }

        onPlayingChanged: {
            if (!playing) {
                updateReconstructionView()
            } else if (playing && (frame + 1 >= frameRange.max + 1)) {
                frame = frameRange.min
            }
            viewer.playback(playing)
        }
    }

    // Update the frame property
    // when the selected view ID is changed externally
    Connections {
        target: _reconstruction
        function onSelectedViewIdChanged() {
            for (let idx = 0; idx < sortedViewIds.length; idx++) {
                if (_reconstruction.selectedViewId === sortedViewIds[idx] && (m.frame != idx)) {
                    m.frame = idx
                }
            }
        }
    }

    // In play mode
    // we use a timer to increment the frame property
    // at a given time rate (defined by the fps property)
    Timer {
        id: timer

        repeat: true
        running: m.playing && root.visible
        interval: 1000 / m.fps

        onTriggered: {
            if (viewer.imageStatus !== Image.Ready) {
                // Wait for current image to be displayed before switching to next image
                return
            }
            let nextIndex = m.frame + 1
            if (nextIndex == frameRange.max + 1) {
                if (m.repeat) {
                    m.frame = frameRange.min
                    return
                }
                else {
                    m.playing = false
                    return
                }
            }
            m.frame = nextIndex
        }
    }
    
    // Widgets:
    // - "Previous Frame" button
    // - "Play - Pause" button
    // - "Next Frame" button
    // - frame label
    // - frame slider
    // - FPS spin box
    // - "Repeat" button
    RowLayout {

        anchors.fill: parent 

        IntSelector {
            id: frameInput

            tooltipText: "Frame"

            value: m.frame
            range: frameRange

            onValueChanged: {
                m.frame = value
            }
        }

        MaterialToolButton {
            id: playButton

            checkable: true
            checked: false
            text: checked ? MaterialIcons.pause_circle : MaterialIcons.play_circle
            font.pointSize: 20
            ToolTip.text: checked ? "Pause Player" : "Play Sequence"

            onCheckedChanged: {
                m.playing = checked
            }

            Connections {
                target: m
                function onPlayingChanged() {
                    playButton.checked = m.playing
                }
            }
        }

    
        Slider {
            id: frameSlider

            Layout.fillWidth: true

            stepSize: 1
            snapMode: Slider.SnapAlways
            live: true

            from: frameRange.min
            to: frameRange.max

            onValueChanged: {
                m.frame = value
            }

            onPressedChanged: {
                if (!pressed) {
                    updateReconstructionView()
                }
            }

            ToolTip {
                parent: frameSlider.handle
                visible: frameSlider.hovered
                text: m.frame
            }

            Connections {
                target: m
                function onFrameChanged() {
                    frameSlider.value = m.frame
                }
            }

            background: Rectangle {
                x: frameSlider.leftPadding
                y: frameSlider.topPadding + frameSlider.height / 2 - height / 2
                width: frameSlider.availableWidth
                height: 4
                radius: 2
                color: Colors.grey

                Repeater {
                    id: cacheView

                    model: viewer ? viewer.cachedFrames : []
                    property real frameLength: sortedViewIds.length > 0 ? frameSlider.width / (frameRange.max - frameRange.min + 1) : 0

                    Rectangle {
                        x: modelData.x * cacheView.frameLength
                        y: 0
                        width: cacheView.frameLength * (modelData.y - modelData.x + 1)
                        height: 4
                        radius: 2
                        color: Colors.blue
                    }
                }
            }
        }

        RowLayout {
            TextInput {
                id: fpsTextInput

                Layout.preferredWidth: fpsMetrics.width
                selectByMouse: true

                text: !focus ? m.fps + " FPS" : m.fps
                color: palette.text

                onEditingFinished: {
                    m.fps = parseInt(text)
                    focus = false
                }
            }
        }

        MaterialToolButton {
            id: fetchButton

            text: MaterialIcons.subscriptions
            ToolTip.text: "Fetch"
            checkable: true
            checked: loading
        }

        MaterialToolButton {
            id: repeatButton

            checkable: true
            checked: false
            text: MaterialIcons.repeat
            ToolTip.text: "Repeat"

            onCheckedChanged: {
                m.repeat = checked
            }
        }

        MaterialToolButton {
            id: infoButton

            text: MaterialIcons.settings
            font.pointSize: 11
            padding: 2
            onClicked: infoMenu.open()
            checkable: true
            checked: infoMenu.visible

            Popup {
                id: infoMenu
                y: parent.height
                x: -width + parent.width

                contentItem: GridLayout {
                        layoutDirection: Qt.LeftToRight
                        columns: 2

                        Column {
                            id: syncColumn
                            Layout.alignment: Qt.AlignTop

                            Text {
                                text: "<b>Synchronisation:</b>"
                                color: palette.text
                            }

                            CheckBox {
                                id: syncFeaturePointsCheckBox
                                text: "Sync Feature Points"
                                checkable: true
                                checked: m.syncFeaturesSelected
                                onCheckedChanged: {
                                    m.syncFeaturesSelected = checked
                                }

                                ToolTip.text: "The Feature points will be updated at the same time as the Sequence Player."
                                ToolTip.visible: hovered
                                ToolTip.delay: 100
                            }

                            CheckBox {
                                id: sync3DCheckBox
                                text: "Sync 3D Viewer"
                                checkable: true
                                checked: m.sync3DSelected
                                onCheckedChanged: {
                                    m.sync3DSelected = checked
                                }

                                ToolTip.text: "The 3D Viewer will be updated at the same time as the Sequence Player."
                                ToolTip.visible: hovered
                                ToolTip.delay: 100
                            }
                        }

                        Column {
                            id: cacheColumn
                            Layout.alignment: Qt.AlignTop

                            Text {
                                text: "<b>Cache:</b>"
                                color: palette.text
                            }

                            // max cache memory limit
                            Row {
                                height: sync3DCheckBox.height
                                Text {
                                    anchors.verticalCenter: parent.verticalCenter
                                    text: "Max Cache Memory: "
                                    color: palette.text
                                }
                                
                                TextField {
                                    id: maxCacheMemoryInput

                                    anchors.verticalCenter: parent.verticalCenter
                                    color: palette.text

                                    text: !focus ? settings_SequencePlayer.maxCacheMemory + " GB" : settings_SequencePlayer.maxCacheMemory

                                    onEditingFinished: {
                                        settings_SequencePlayer.maxCacheMemory = parseInt(text)
                                        focus = false
                                    }
                                }
                            }

                            Text {
                                height: sync3DCheckBox.height
                                verticalAlignment: Text.AlignVCenter
                                text: {
                                    if (viewer && viewer.ramInfo != undefined)
                                        return "Available Memory: " + viewer.ramInfo.x + " GB"
                                    return "Unknown Available Memory"
                                }
                                color: palette.text
                            }

                            Text {
                                height: sync3DCheckBox.height
                                verticalAlignment: Text.AlignVCenter
                                text: {
                                    // number of cached frames is the difference between the first and last frame of all intervals in the cache
                                    let cachedFrames = viewer ? viewer.cachedFrames : []
                                    let cachedFramesCount = 0
                                    for (let i = 0; i < cachedFrames.length; i++) {
                                        cachedFramesCount += cachedFrames[i].y - cachedFrames[i].x + 1
                                    }
                                    return "Cached Frames: " + (viewer ? cachedFramesCount : "0") + " / " + sortedViewIds.length
                                }
                                color: palette.text
                            }

                            // do beautiful progress bar
                            ProgressBar {
                                id: cacheProgressBar

                                width: parent.width

                                from: 0
                                to: viewer && viewer.ramInfo != undefined ? viewer.ramInfo.x : 0

                                value: viewer ? settings_SequencePlayer.maxCacheMemory : 0

                                ToolTip.text: {
                                    let ramMsg = "Max cache memory set: " + settings_SequencePlayer.maxCacheMemory + " GB"
                                    if (viewer && viewer.ramInfo != undefined) {
                                        return  ramMsg + "\n" + "on available memory: " + viewer.ramInfo.x + " GB"
                                    }
                                    return ramMsg + ",\n" + "available memory unknown"
                                }
                                ToolTip.visible: hovered
                                ToolTip.delay: 100
                            }

                            ProgressBar {
                                id: occupiedCacheProgressBar

                                property string occupiedCache: viewer && viewer.ramInfo ? Format.GB2SizeStr(viewer.ramInfo.y) : 0

                                width: parent.width

                                from: 0
                                to: settings_SequencePlayer.maxCacheMemory
                                value: viewer && viewer.ramInfo != undefined ? viewer.ramInfo.y : 0

                                ToolTip.text: "Occupied cache: " + occupiedCache + "\n" + "On max cache memory set: " + settings_SequencePlayer.maxCacheMemory + " GB"
                                ToolTip.visible: hovered
                                ToolTip.delay: 100
                            }
                            
                        }
                    }
            }
        }
    }

    TextMetrics {
        id: fpsMetrics

        font: fpsTextInput.font
        text: "100 FPS"
    }

    // Action to play/pause the sequence player
    Action {
        id: playPauseAction

        shortcut: "Space"

        onTriggered: {
            m.playing = !m.playing
        }
    }
}
