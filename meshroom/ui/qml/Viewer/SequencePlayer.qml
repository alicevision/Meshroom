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

    function updateSceneView() {
        if (isOutputSequence || m.updatingRange)
            return
        if (_currentScene && m.frame >= 0 && m.frame < sortedViewIds.length) {
            if (!m.playing && !frameSlider.pressed) {
                _currentScene.selectedViewId = sortedViewIds[m.frame]
            } else {
                _currentScene.pickedViewId = sortedViewIds[m.frame]
                if (m.sync3DSelected) {
                    _currentScene.updateSelectedViewpoint(_currentScene.pickedViewId)
                }
            }
        }
    }

    // sortedViewIds and isOutputSequence are updated separately, in any order:
    // re-sync on both, the selection is only followed once both are consistent.
    onIsOutputSequenceChanged: updateRange()
    onSortedViewIdsChanged: updateRange()
    Component.onCompleted: updateRange()

    // Set the current frame without changing the scene selection
    // (for frame changes caused by a change of the frame range, not by the user)
    function setFrameSilently(frame) {
        m.updatingRange = true
        m.frame = frame
        m.updatingRange = false
    }

    // Index of the scene's selected view in sortedViewIds (-1 if not found)
    function selectedViewIndex() {
        if (isOutputSequence || !_currentScene)
            return -1
        const selectedId = String(_currentScene.selectedViewId)
        return sortedViewIds.findIndex(viewId => String(viewId) === selectedId)
    }

    // Move the current frame to the view selected in the scene (e.g. from the ImageGallery)
    function syncFrameWithSelectedView() {
        const idx = selectedViewIndex()
        if (idx >= 0 && m.frame !== idx)
            m.frame = idx
    }

    function updateRange() {
        // frameRange is mutated in place by the owner of sortedViewIds, which does not notify:
        // propagate it explicitly to the widgets.
        if (sortedViewIds.length === 0) {
            // No image: reset to an empty range and stop the playback (the play button is disabled)
            frameRange.min = 0
            frameRange.max = 0
            m.playing = false
        }
        const min = frameRange.min
        const max = Math.max(frameRange.min, frameRange.max)

        // Changing the range clamps the slider/selector values: do not let that change the scene selection
        m.updatingRange = true
        frameSlider.from = min
        frameSlider.to = max
        frameInput.range = { "min": min, "max": max }
        const idx = selectedViewIndex()
        if (idx >= 0)
            m.frame = idx
        else if (m.frame < min || m.frame > max)
            m.frame = min
        m.updatingRange = false
        // Clamping may have desynchronized the slider from the current frame: restore the binding
        frameSlider.value = Qt.binding(function() { return m.frame })
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
        property bool updatingRange: false  // true while the frame range is being updated

        onFrameChanged: {
            updateSceneView()
        }

        onPlayingChanged: {
            updateSceneView()
            if (playing && (frame + 1 >= frameRange.max + 1)) {
                frame = frameRange.min
            }
            if (viewer)
                viewer.playback(playing)
        }
    }

    // Update the frame property
    // when the selected view ID is changed externally
    Connections {
        target: _currentScene
        function onSelectedViewIdChanged() {
            syncFrameWithSelectedView()
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
            if (!viewer) {
                // No HDR viewer (e.g. 8-bit viewer): it cannot report the image status, stop the playback
                m.playing = false
                return
            }
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
            enabled: sortedViewIds.length > 0

            tooltipText: "Frame"
            displayButtons: true

            // range is set by updateRange(): frameRange is mutated in place and does not notify

            onValueChanged: {
                if (!m.updatingRange)
                    m.frame = value
            }

            Binding {
                target: frameInput
                property: "value"
                value: m.frame
                when: !frameInput.activeFocus
            }
        }

        MaterialToolButton {
            id: playButton
            enabled: sortedViewIds.length > 0

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

    
        TimelineSlider {
            id: frameSlider
            enabled: sortedViewIds.length > 0

            Layout.fillWidth: true

            value: m.frame

            stepSize: 1
            snapMode: Slider.SnapAlways
            live: true

            from: frameRange.min
            to: frameRange.max

            cachedFrames: viewer && sortedViewIds.length > 0 ? viewer.cachedFrames : []

            onValueChanged: {
                if (!m.updatingRange)
                    m.frame = value
            }

            onPressedChanged: {
                if (!pressed) {
                    updateSceneView()
                }
            }

            ToolTip {
                parent: frameSlider.handle
                visible: frameSlider.hovered
                text: m.frame
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
