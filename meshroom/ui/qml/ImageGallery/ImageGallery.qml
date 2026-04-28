import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQml.Models
import Qt.labs.qmlmodels

import Controls 1.0
import MaterialIcons 2.2
import Utils 1.0

/**
 * ImageGallery displays as a grid of Images a model containing Viewpoints objects.
 * It manages a model of multiple CameraInit nodes as individual groups.
 */

Panel {
    id: root

    property variant cameraInits
    property variant cameraInit
    property int cameraInitIndex
    property variant tempCameraInit

    readonly property var currentItem: layoutLoader.item ? layoutLoader.item.currentItem : null
    readonly property string currentItemSource: currentItem ? currentItem.source : ""
    readonly property var currentItemMetadata: currentItem ? currentItem.metadata : undefined
    readonly property int centerViewId: (_currentScene && _currentScene.sfmTransform) ? parseInt(_currentScene.sfmTransform.attribute("transformation").value) : 0
    readonly property var galleryGrid: layoutLoader.item  // This now references the loaded view (grid or list)

    property int defaultCellSize: 160
    property bool readOnly: false

    enum LayoutModes {
        Grid=0,
        List=1
    }

    property int displayMode: ImageGallery.LayoutModes.Grid

    property var filesByType: ({})
    property int nbMeshroomScenes: 0
    property int nbDraggedFiles: 0

    signal removeSelectedImagesRequest(var objects)
    signal allViewpointsCleared()
    signal filesDropped(var drop)

    title: "Image Gallery"
    implicitWidth: (root.defaultCellSize + 2) * 2

    Connections {
        target: _currentScene

        function onCameraInitChanged() {
            nodesCB.currentIndex = root.cameraInitIndex
            sortedModel.clearMultiSelection(false)
        }
    }

    QtObject {
        id: m
        property variant currentCameraInit: _currentScene && _currentScene.tempCameraInit ? _currentScene.tempCameraInit : root.cameraInit
        property variant viewpoints: currentCameraInit ? currentCameraInit.attribute('viewpoints').value : undefined
        property variant intrinsics: currentCameraInit ? currentCameraInit.attribute('intrinsics').value : undefined
        property bool readOnly: ((_currentScene && currentCameraInit) ? currentCameraInit.locked : root.readOnly) || displayHDR.checked

        onViewpointsChanged: {
            ThumbnailCache.clearRequests()
        }

        onIntrinsicsChanged: {
            parseIntr()
        }
    }

    property variant parsedIntrinsic
    property int numberOfIntrinsics: m.intrinsics ? m.intrinsics.count : 0
    onNumberOfIntrinsicsChanged: {
        parseIntr()
    }

    function changeCurrentIndex(newIndex) {
        _currentScene.cameraInitIndex = newIndex
    }

    function populate_model() {
        if (!intrinsicModel.ready) {
            // If the TableModel is not done being instantiated, do nothing
            return
        }

        intrinsicModel.clear()
        for (var intr in parsedIntrinsic) {
            intrinsicModel.appendRow(parsedIntrinsic[intr])
        }
    }

    function parseIntr() {
        parsedIntrinsic = []
        if (!m.intrinsics) {
            return
        }

        // Loop through all intrinsics
        for (var i = 0; i < m.intrinsics.count; ++i) {
            var intrinsic = {}

            // Loop through all attributes
            for (var j = 0; j < m.intrinsics.at(i).value.count; ++j) {
                var currentAttribute = m.intrinsics.at(i).value.at(j)
                if (currentAttribute.type === "GroupAttribute") {
                    for (var k = 0; k < currentAttribute.value.count; ++k) {
                        intrinsic[currentAttribute.name + "." + currentAttribute.value.at(k).name] = currentAttribute.value.at(k)
                    }
                } else if (currentAttribute.type === "ListAttribute") {
                    // Not needed for now
                } else {
                    intrinsic[currentAttribute.name] = currentAttribute
                }
            }
            // Table Model needs to contain an entry for each column.
            // In case of old file formats, some intrinsic keys that we display may not exist in the model.
            // So, here we create an empty entry to enforce that the key exists in the model.
            for (var n = 0; n < intrinsicModel.columnNames.length; ++n) {
                var name = intrinsicModel.columnNames[n]
                if (!(name in intrinsic)) {
                    intrinsic[name] = {}
                }
            }
            parsedIntrinsic[i] = intrinsic
        }
        populate_model()
    }

    function toggleDisplayMode() {
        displayMode = displayMode === ImageGallery.LayoutModes.Grid ? 
            ImageGallery.LayoutModes.List : ImageGallery.LayoutModes.Grid
    }

    headerBar: RowLayout {
        SearchBar {
            id: searchBar
            toggle: true  // Enable toggling the actual text field by the search button
            Layout.minimumWidth: searchBar.width
            maxWidth: 150
        }

        MaterialToolButton {
            text: root.displayMode === ImageGallery.LayoutModes.Grid ? MaterialIcons.view_list : MaterialIcons.view_module
            font.pointSize: 11
            padding: 2
            ToolTip.text: "Switch the layout to " + root.displayMode === ImageGallery.LayoutModes.Grid ? "List" : "Grid"
            ToolTip.visible: hovered
            onClicked: root.toggleDisplayMode()
        }

        MaterialToolButton {
            text: MaterialIcons.more_vert
            font.pointSize: 11
            padding: 2
            checkable: true
            checked: galleryMenu.visible
            onClicked: galleryMenu.open()
            Menu {
                id: galleryMenu
                y: parent.height
                x: -width + parent.width
                MenuItem {
                    text: "Edit Sensor Database..."
                    onTriggered: {
                        sensorDBDialog.open()
                    }
                }

                Menu {
                    title: "Advanced"
                    Action {
                        id: displayViewIdsAction
                        text: "Display View IDs"
                        checkable: true
                    }
                }
            }
        }
    }

    SensorDBDialog {
        id: sensorDBDialog
        sensorDatabase: cameraInit ? Filepath.stringToUrl(cameraInit.attribute("sensorDatabase").evalValue) : ""
        readOnly: _currentScene ? _currentScene.computing : false
        onUpdateIntrinsicsRequest: _currentScene.rebuildIntrinsics(cameraInit)
    }

    SortFilterDelegateModel {
        id: sortedModel
        model: m.viewpoints
        sortRole: "path.basename"
        filters: displayViewIdsAction.checked ? filtersWithViewIds : filtersBasic
        property var filtersBasic: [
            {role: "path", value: searchBar.text},
            {role: "viewId.isReconstructed", value: reconstructionFilter}
        ]
        property var filtersWithViewIds:  [
            [
                {role: "path", value: searchBar.text}, 
                {role: "viewId.asString", value: searchBar.text}
            ], 
            {role: "viewId.isReconstructed", value: reconstructionFilter}
        ]
        property var reconstructionFilter: undefined

        // Override modelData to return basename of viewpoint's path for sorting
        function modelData(item, roleName_) {
            var roleNameAndCmd = roleName_.split(".")
            var roleName = roleName_
            var cmd = ""
            if (roleNameAndCmd.length >= 2) {
                roleName = roleNameAndCmd[0]
                cmd = roleNameAndCmd[1]
            }
            if (cmd === "isReconstructed")
                return _currentScene.isReconstructed(item.model.object);

            var value = item.model.object.childAttribute(roleName).value;
            if (cmd === "basename")
                return Filepath.basename(value);
            if (cmd === "asString") 
                return value.toString();

            return value
        }

        property int selectedIndex: -1
        property var selectedIndices: []

        function toggleIndex(idx) {
            var newArr = selectedIndices.slice()
            var pos = newArr.indexOf(idx)
            if (pos >= 0) {
                newArr.splice(pos, 1)
            } else {
                newArr.push(idx)
            }
            selectedIndices = newArr
        }

        function selectRange(from, to) {
            var newArr = []
            var start = Math.min(from, to)
            var end = Math.max(from, to)
            for (var i = start; i <= end; i++) {
                newArr.push(i)
            }
            selectedIndices = newArr
        }

        function clearMultiSelection(keepPosition) {
            if (keepPosition) {
                // Pick the lowest selected index as the landing position; after removal
                // the next surviving item slides up to that slot.
                // Clamp to the last remaining item in case the selection was at the tail.
                var sortedSel = selectedIndices.slice().sort(function(a, b){ return a - b })
                var remainingCount = count - selectedIndices.length
                selectedIndex = Math.min(sortedSel[0], remainingCount - 1)
                selectedIndices = [selectedIndex]
            } else {
                selectedIndex = -1
                selectedIndices = []
            }
        }

        delegate: ImageDelegate {
            id: imageDelegate

            layoutMode: root.displayMode
            viewpoint: object.value
            cellID: DelegateModel.filteredIndex
            width: layoutLoader.item ? (displayMode === ImageGallery.LayoutModes.List ? layoutLoader.item.width : layoutLoader.item.cellWidth) : 0
            height: layoutLoader.item ? layoutLoader.item.cellHeight : 0

            readOnly: m.readOnly
            displayViewId: displayViewIdsAction.checked
            displayThumbnail: thumbnailSizeSlider.value > thumbnailSizeSlider.from
            visible: !intrinsicsFilterButton.checked
            
            parentModel: sortedModel

            onPressed: function(mouse) {
                if (mouse.button !== Qt.LeftButton)
                    return
                if (layoutLoader.item) {
                    var idx = DelegateModel.filteredIndex
                    if (mouse.modifiers & Qt.ShiftModifier && sortedModel.selectedIndex >= 0) {
                        // Range select from last selectedIndex to clicked item
                        sortedModel.selectRange(sortedModel.selectedIndex, idx)
                    } else if (mouse.modifiers & Qt.ControlModifier) {
                        // Toggle this item's selection
                        sortedModel.toggleIndex(idx)
                        // If the item is being removed from the selection, then we should return
                        // before setting the current index: this prevents highlighting the item which is being
                        // removed, as it could be confusing for the user
                        if (sortedModel.selectedIndices.indexOf(idx) < 0) {
                            if (sortedModel.selectedIndices.length === 0) {
                                // Last item deselected: clear the viewer entirely
                                sortedModel.selectedIndex = -1
                                layoutLoader.item.currentIndex = -1
                                _currentScene.selectedViewId = "-1"
                            } else if (idx === sortedModel.selectedIndex) {
                                // The currently viewed item was deselected: move to the
                                // closest remaining selected item.
                                var remaining = sortedModel.selectedIndices
                                var next = remaining[0]
                                var minDist = Math.abs(remaining[0] - idx)
                                for (var r = 1; r < remaining.length; r++) {
                                    var dist = Math.abs(remaining[r] - idx)
                                    if (dist < minDist) {
                                        minDist = dist
                                        next = remaining[r]
                                    }
                                }
                                sortedModel.selectedIndex = next
                                layoutLoader.item.currentIndex = next
                            }
                            return
                        }
                    } else {
                        // Normal click: clear multi-selection, select only this item
                        sortedModel.selectedIndices = [idx]
                    }
                    // Update selectedIndex before currentIndex to prevent onCurrentItemChanged
                    // from incorrectly resetting the multi-selection
                    sortedModel.selectedIndex = idx
                    layoutLoader.item.currentIndex = idx
                }
            }

            function sendRemoveSelectedRequest() {
                if (readOnly)
                    return

                // Capture delegate-scope references immediately: this prevents falling into
                // cases where "sortedModel" is unresolvable because the delegate has been destroyed before
                // the line accessing "sortedModel" is reached
                var model = sortedModel
                var view = root.galleryGrid

                // If all the images are selected, we can just remove all of them at once
                if (model.selectedIndices.length === m.viewpoints.count) {
                    removeAllImages()
                    return
                }

                var objects = []
                for (var i = 0; i < model.selectedIndices.length; i++) {
                    var obj = model.getObjectAt(model.selectedIndices[i])
                    if (obj)
                        objects.push(obj)
                }
                if (objects.length > 0) {
                    root.removeSelectedImagesRequest(objects)
                    model.clearMultiSelection(true)

                    // Restore a sensible position once the model has finished updating
                    var targetIndex = model.selectedIndex
                    Qt.callLater(function() {
                        if (targetIndex >= 0 && view) {
                            view.currentIndex = targetIndex
                            view.makeCurrentItemVisible()
                        }
                    })
                }

                // If the last image has been removed, make sure the viewpoints and intrinsics are reset
                if (m.viewpoints !== undefined && m.viewpoints.count === 0)
                    root.allViewpointsCleared()
            }

            function removeAllImages() {
                _currentScene.removeAllImages()
                _currentScene.selectedViewId = "-1"
            }

            onRemoveSelectedRequest: sendRemoveSelectedRequest()
            Keys.onPressed: function(event) {
                if (event.key === Qt.Key_Delete && event.modifiers === Qt.ShiftModifier) {
                    removeAllImages()
                } else if (event.key === Qt.Key_Delete) {
                    sendRemoveSelectedRequest()
                }
            }
            onRemoveAllImagesRequest: {
                removeAllImages()
            }

            RowLayout {
                anchors.top: parent.top
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.margins: 2
                spacing: 2

                property bool valid: Qt.isQtObject(object) // object can be evaluated to null at some point during creation/deletion
                property bool inViews: valid && _currentScene && _currentScene.sfmReport && _currentScene.isInViews(object)

                // Camera Initialization indicator
                IntrinsicsIndicator {
                    intrinsic: parent.valid && _currentScene ? _currentScene.getIntrinsic(object) : null
                    metadata: imageDelegate.metadata
                }

                // Rig indicator
                Loader {
                    id: rigIndicator
                    property int rigId: parent.valid ? object.childAttribute("rigId").value : -1
                    active: rigId >= 0
                    sourceComponent: ImageBadge {
                        property int rigSubPoseId: model.object.childAttribute("subPoseId").value
                        text: MaterialIcons.link
                        ToolTip.text: "<b>Rig: Initialized</b><br>" +
                                        "Rig ID: " + rigIndicator.rigId + " <br>" +
                                        "SubPose: " + rigSubPoseId
                    }
                }

                // Center of SfMTransform
                Loader {
                    id: sfmTransformIndicator
                    active: viewpoint && (viewpoint.get("viewId").value === centerViewId)
                    sourceComponent: ImageBadge {
                        text: MaterialIcons.gamepad
                        ToolTip.text: "Camera used to define the center of the scene."
                    }
                }

                Item { Layout.fillWidth: true }

                // Reconstruction status indicator
                Loader {
                    active: parent.inViews
                    visible: active
                    sourceComponent: ImageBadge {
                        property bool reconstructed: _currentScene.sfmReport && _currentScene.isReconstructed(model.object)
                        text: reconstructed ? MaterialIcons.videocam : MaterialIcons.videocam_off
                        color: reconstructed ? Colors.green : Colors.red
                        ToolTip.text: "<b>Camera: " + (reconstructed ? "" : "Not ") + "Reconstructed</b>"
                    }
                }
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 4

        Loader {
            id: layoutLoader
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: !intrinsicsFilterButton.checked
            
            sourceComponent: root.displayMode === ImageGallery.LayoutModes.Grid ? gridViewComponent : listViewComponent
            
            onLoaded: {
                if (item) {
                    // Pass necessary properties to the loaded component
                    item.m = m
                    item.gallery = root
                    item.searchBar = searchBar
                    item.intrinsicsFilterButton = intrinsicsFilterButton
                    item.tempCameraInit = tempCameraInit
                    item.errorDialog = errorDialog
                    item.sortedModel = sortedModel
                    item.thumbnailSizeSlider = thumbnailSizeSlider

                    // Connect signals
                    item.allViewpointsCleared.connect(root.allViewpointsCleared)
                    
                    // Restore currentIndex (before connecting signals to avoid unwanted selection change)
                    item.currentIndex = sortedModel.selectedIndex
                    
                    // Don't scroll yet because we must make sure the layout is loaded first
                    scrollTimer.restart()
                }
            }
        }

        // Add a timer with a small delay so that we scroll after loading the layout
        Timer {
            id: scrollTimer
            interval: 25
            repeat: false
            onTriggered: {
                if (layoutLoader.item && _currentScene.selectedViewId > -1) {
                    layoutLoader.item.updateCurrentIndexFromSelectionViewId()
                    // Use another short delay for the actual scroll
                    Qt.callLater(function() {
                        if (layoutLoader.item && layoutLoader.item.currentIndex >= 0) {
                            layoutLoader.item.makeCurrentItemVisible()
                        }
                    })
                }
            }
        }
        
        Component {
            id: gridViewComponent
            ImageGridView {
                id: gridView
            }
        }

        Component {
            id: listViewComponent
            ImageListView {
                id: listView
            }
        }

        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: intrinsicsFilterButton.checked
            clip: true

            TableView {
                id : intrinsicTable
                visible: intrinsicsFilterButton.checked
                anchors.fill: parent
                boundsMovement : Flickable.StopAtBounds

                palette: root.palette

                // Provide width for column
                // Note no size provided for the last column (bool comp) so it uses its automated size
                columnWidthProvider: function (column) { return intrinsicModel.columnWidths[column] }

                model: intrinsicModel

                delegate: IntrinsicDisplayDelegate {
                    attribute: model.display
                    readOnly: m.currentCameraInit ? m.currentCameraInit.locked : false
                }

                ScrollBar.horizontal: MScrollBar { id: sb }
                ScrollBar.vertical : MScrollBar { id: sbv }
            }

            TableModel {
                id : intrinsicModel
                property bool ready: false

                // Hardcoded default width per column
                property var columnWidths: [105, 75, 75, 75, 60, 60, 60, 60, 200, 60, 60, 60]
                property var columnNames: [
                    "intrinsicId",
                    "initialFocalLength",
                    "focalLength",
                    "type",
                    "width",
                    "height",
                    "sensorWidth",
                    "sensorHeight",
                    "serialNumber",
                    "principalPoint.x",
                    "principalPoint.y",
                    "locked"
                ]

                TableModelColumn { display: function(modelIndex){return parsedIntrinsic[modelIndex.row][intrinsicModel.columnNames[0]]} }
                TableModelColumn { display: function(modelIndex){return parsedIntrinsic[modelIndex.row][intrinsicModel.columnNames[1]]} }
                TableModelColumn { display: function(modelIndex){return parsedIntrinsic[modelIndex.row][intrinsicModel.columnNames[2]]} }
                TableModelColumn { display: function(modelIndex){return parsedIntrinsic[modelIndex.row][intrinsicModel.columnNames[3]]} }
                TableModelColumn { display: function(modelIndex){return parsedIntrinsic[modelIndex.row][intrinsicModel.columnNames[4]]} }
                TableModelColumn { display: function(modelIndex){return parsedIntrinsic[modelIndex.row][intrinsicModel.columnNames[5]]} }
                TableModelColumn { display: function(modelIndex){return parsedIntrinsic[modelIndex.row][intrinsicModel.columnNames[6]]} }
                TableModelColumn { display: function(modelIndex){return parsedIntrinsic[modelIndex.row][intrinsicModel.columnNames[7]]} }
                TableModelColumn { display: function(modelIndex){return parsedIntrinsic[modelIndex.row][intrinsicModel.columnNames[8]]} }
                TableModelColumn { display: function(modelIndex){return parsedIntrinsic[modelIndex.row][intrinsicModel.columnNames[9]]} }
                TableModelColumn { display: function(modelIndex){return parsedIntrinsic[modelIndex.row][intrinsicModel.columnNames[10]]} }
                TableModelColumn { display: function(modelIndex){return parsedIntrinsic[modelIndex.row][intrinsicModel.columnNames[11]]} }
                //https://doc.qt.io/qt-5/qml-qt-labs-qmlmodels-tablemodel.html#appendRow-method

                Component.onCompleted: {
                    ready = true
                    // Triggers "populate_model" in case the intrinsics have been filled while the model was
                    // being instantiated
                    root.populate_model()
                }
            }

            //CODE FOR HEADERS
            //UNCOMMENT WHEN COMPATIBLE WITH THE RIGHT QT VERSION
            // HorizontalHeaderView {
            //     id: horizontalHeader
            //     syncView: tableView
            //     anchors.left: tableView.left
            // }
        }

        RowLayout {
            Layout.fillHeight: false
            visible: root.cameraInits ? root.cameraInits.count > 1 : false
            Layout.alignment: Qt.AlignHCenter
            spacing: 2

            ToolButton {
                text: MaterialIcons.navigate_before
                property string previousGroupName: {
                    if (root.cameraInits && root.cameraInitIndex - 1 >= 0) {
                        return root.cameraInits.at(root.cameraInitIndex - 1).label
                    }
                    return ""
                }
                font.family: MaterialIcons.fontFamily
                ToolTip.text: "Previous Group (Alt+Left): " + previousGroupName
                ToolTip.visible: hovered
                enabled: nodesCB.currentIndex > 0
                onClicked: nodesCB.decrementCurrentIndex()
            }
            Label {
                id: groupLabel
                text: "Group "
            }
            ComboBox {
                id: nodesCB
                model: {
                    // Create an array from 1 to cameraInits.count for the
                    // display of group indices (real indices still are from
                    // 0 to cameraInits.count - 1)
                    var l = [];
                    if (root.cameraInits) {
                        for (var i = 1; i <= root.cameraInits.count; i++) {
                            l.push(i);
                        }
                    }
                    return l;
                }
                implicitWidth: 40
                currentIndex: root.cameraInitIndex
                onActivated: root.changeCurrentIndex(currentIndex)
            }
            Label { text: "/ " + (root.cameraInits ? root.cameraInits.count : "Unknown") }
            ToolButton {
                text: MaterialIcons.navigate_next
                property string nextGroupName: {
                    if (root.cameraInits && root.cameraInitIndex + 1 < root.cameraInits.count) {
                        var group = root.cameraInits.at(root.cameraInitIndex + 1)
                        if (group)
                            return root.cameraInits.at(root.cameraInitIndex + 1).label
                    }
                    return ""
                }
                font.family: MaterialIcons.fontFamily
                ToolTip.text: "Next Group (Alt+Right): " + nextGroupName
                ToolTip.visible: hovered
                enabled: root.cameraInits ? nodesCB.currentIndex < root.cameraInits.count - 1 : false
                onClicked: nodesCB.incrementCurrentIndex()
            }
        }

        RowLayout {
            Layout.fillHeight: false
            Layout.alignment: Qt.AlignHCenter
            visible: root.cameraInits ? root.cameraInits.count > 1 : false

            Label {
                id: groupName
                text: root.cameraInit ? "<b>" + root.cameraInit.label + "</b>" + (root.cameraInit.label !== root.cameraInit.defaultLabel ? " (" + root.cameraInit.defaultLabel + ")" : "") : ""
                font.pointSize: 8
            }
        }
    }

    footerContent: RowLayout {
        // Images count
        id: footer

        function resetButtons() {
            inputImagesFilterButton.checked = false
            estimatedCamerasFilterButton.checked = false
            nonEstimatedCamerasFilterButton.checked = false
        }

        MaterialToolLabelButton {
            id : inputImagesFilterButton
            Layout.minimumWidth: childrenRect.width
            ToolTip.text: (layoutLoader.item && layoutLoader.item.model ? layoutLoader.item.model.count : 0) + " Input Images"
            iconText: MaterialIcons.image
            label: (m.viewpoints ? m.viewpoints.count : 0)
            padding: 3

            checkable: true
            checked: true

            onCheckedChanged: {
                if (checked) {
                    sortedModel.reconstructionFilter = undefined;
                    estimatedCamerasFilterButton.checked = false;
                    nonEstimatedCamerasFilterButton.checked = false;
                    intrinsicsFilterButton.checked = false;
                } else {
                    if (estimatedCamerasFilterButton.checked === false && nonEstimatedCamerasFilterButton.checked === false && intrinsicsFilterButton.checked === false)
                        inputImagesFilterButton.checked = true
                }
            }
        }
        // Estimated cameras count
        MaterialToolLabelButton {
            id : estimatedCamerasFilterButton
            Layout.minimumWidth: childrenRect.width
            ToolTip.text: label + " Estimated Cameras"
            iconText: MaterialIcons.videocam
            label: _currentScene && _currentScene.nbCameras ? _currentScene.nbCameras.toString() : "-"
            padding: 3

            enabled: _currentScene ? _currentScene.cameraInit && _currentScene.nbCameras : false
            checkable: true
            checked: false

            onCheckedChanged: {
                if (checked) {
                    sortedModel.reconstructionFilter = true
                    inputImagesFilterButton.checked = false
                    nonEstimatedCamerasFilterButton.checked = false
                    intrinsicsFilterButton.checked = false
                } else {
                    if (inputImagesFilterButton.checked === false && nonEstimatedCamerasFilterButton.checked === false && intrinsicsFilterButton.checked === false)
                        inputImagesFilterButton.checked = true
                }
            }
            onEnabledChanged: {
                if (!enabled) {
                    if (checked)
                        inputImagesFilterButton.checked = true
                    checked = false
                }
            }
        }

        // Non estimated cameras count
        MaterialToolLabelButton {
            id : nonEstimatedCamerasFilterButton
            Layout.minimumWidth: childrenRect.width
            ToolTip.text: label + " Non Estimated Cameras"
            iconText: MaterialIcons.videocam_off
            label: _currentScene && _currentScene.nbCameras ? ((m.viewpoints ? m.viewpoints.count : 0) - _currentScene.nbCameras.toString()).toString() : "-"
            padding: 3

            enabled: _currentScene ? _currentScene.cameraInit && _currentScene.nbCameras : false
            checkable: true
            checked: false

            onCheckedChanged: {
                if (checked) {
                    sortedModel.reconstructionFilter = false
                    inputImagesFilterButton.checked = false
                    estimatedCamerasFilterButton.checked = false
                    intrinsicsFilterButton.checked = false
                } else {
                    if (inputImagesFilterButton.checked === false && estimatedCamerasFilterButton.checked === false && intrinsicsFilterButton.checked === false)
                        inputImagesFilterButton.checked = true
                }
            }
            onEnabledChanged: {
                if (!enabled) {
                    if (checked)
                        inputImagesFilterButton.checked = true
                    checked = false
                }
            }
        }

        MaterialToolLabelButton {
            id : intrinsicsFilterButton
            Layout.minimumWidth: childrenRect.width
            ToolTip.text: label + " Number of intrinsics"
            iconText: MaterialIcons.camera
            label: _currentScene ? (m.intrinsics ? m.intrinsics.count : 0) : "0"
            padding: 3

            enabled: m.intrinsics ? m.intrinsics.count > 0 : false
            checkable: true
            checked: false

            onCheckedChanged: {
                if (checked) {
                    inputImagesFilterButton.checked = false
                    estimatedCamerasFilterButton.checked = false
                    nonEstimatedCamerasFilterButton.checked = false
                } else {
                    if (inputImagesFilterButton.checked === false && estimatedCamerasFilterButton.checked === false && nonEstimatedCamerasFilterButton.checked === false)
                        inputImagesFilterButton.checked = true
                }
            }
            onEnabledChanged: {
                if (!enabled) {
                    if (checked)
                        inputImagesFilterButton.checked = true
                    checked = false
                }
            }
        }

        Item {
            Layout.fillHeight: true
            Layout.fillWidth: true
        }

        MaterialToolLabelButton {
            id: displayHDR
            Layout.minimumWidth: childrenRect.width
            property var activeNode: _currentScene ? _currentScene.activeNodes.get("LdrToHdrMerge").node : null
            ToolTip.text: "Visualize HDR images: " + (activeNode ? activeNode.label : "No Node")
            iconText: MaterialIcons.filter
            label: activeNode ? activeNode.attribute("nbBrackets").value : ""
            visible: activeNode
            enabled: activeNode && activeNode.isComputed && (m.viewpoints ? m.viewpoints.count > 0 : false)
            property string nodeID: activeNode ? (activeNode.label + activeNode.isComputed) : ""
            onNodeIDChanged: {
                if (checked) {
                    open()
                }
            }
            onEnabledChanged: {
                // Reset the toggle to avoid getting stuck with the HDR node checked but disabled
                if (checked) {
                    checked = false
                    close()
                }
            }
            checkable: true
            checked: false
            onClicked: {
                if (checked) {
                    open()
                } else {
                    close()
                }
            }
            function open() {
                if (imageProcessing.checked)
                    imageProcessing.checked = false
                _currentScene.setupTempCameraInit(activeNode, "outSfMData")
            }
            function close() {
                _currentScene.clearTempCameraInit()
            }
        }

        MaterialToolButton {
            id: imageProcessing
            Layout.minimumWidth: childrenRect.width

            property var activeNode: _currentScene ? _currentScene.activeNodes.get("ImageProcessing").node : null
            font.pointSize: 15
            padding: 0
            ToolTip.text: "Preprocessed Images: " + (activeNode ? activeNode.label : "No Node")
            text: MaterialIcons.wallpaper
            visible: activeNode && activeNode.attribute("outSfMData").value
            enabled: activeNode && activeNode.isComputed
            property string nodeID: activeNode ? (activeNode.label + activeNode.isComputed) : ""
            onNodeIDChanged: {
                if (checked) {
                    open()
                }
            }
            onEnabledChanged: {
                // Reset the toggle to avoid getting stuck with the HDR node checked but disabled
                if (checked) {
                    checked = false
                    close()
                }
            }
            checkable: true
            checked: false
            onClicked: {
                if (checked) {
                    open()
                } else {
                    close()
                }
            }
            function open() {
                if (displayHDR.checked)
                    displayHDR.checked = false
                _currentScene.setupTempCameraInit(activeNode, "outSfMData")
            }
            function close() {
                _currentScene.clearTempCameraInit()
            }
        }

        Item {
            Layout.fillHeight: true
            width: 1
        }

        // Thumbnail size icon and slider
        MaterialToolButton {
            Layout.minimumWidth: childrenRect.width

            text: MaterialIcons.photo_size_select_large
            ToolTip.text: "Thumbnails Scale"
            padding: 0
            anchors.margins: 0
            font.pointSize: 11
            onClicked: { thumbnailSizeSlider.value = defaultCellSize }
        }
        Slider {
            id: thumbnailSizeSlider
            from: 70
            value: defaultCellSize
            to: 250
            implicitWidth: 70
        }
    }

    MessageDialog {
        id: errorDialog

        icon.text: MaterialIcons.error
        icon.color: "#F44336"

        title: "Different File Types"
        text: "Do not mix .mg files and other types of files."
        standardButtons: Dialog.Ok

        parent: Overlay.overlay

        onAccepted: close()
    }
}
