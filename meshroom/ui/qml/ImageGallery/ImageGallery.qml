import QtQuick 2.14
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3
import MaterialIcons 2.2
import QtQml.Models 2.2
import Qt.labs.qmlmodels 1.0

import Controls 1.0
import Utils 1.0

/**
 * ImageGallery displays as a grid of Images a model containing Viewpoints objects.
 * It manages a model of multiple CameraInit nodes as individual groups.
 */
Panel {
    id: root

    property variant cameraInits
    property variant cameraInit
    property variant tempCameraInit
    readonly property alias currentItem: grid.currentItem
    readonly property string currentItemSource: grid.currentItem ? grid.currentItem.source : ""
    readonly property var currentItemMetadata: grid.currentItem ? grid.currentItem.metadata : undefined
    readonly property int centerViewId: (_reconstruction && _reconstruction.sfmTransform) ? parseInt(_reconstruction.sfmTransform.attribute("transformation").value) : 0

    property int defaultCellSize: 160
    property int currentIndex: 0
    property bool readOnly: false

    property string filter: ""
    property bool filterValue: true

    signal removeImageRequest(var attribute)
    signal filesDropped(var drop, var augmentSfm)

    title: "Images"
    implicitWidth: (root.defaultCellSize + 2) * 2

    function changeCurrentIndex(newIndex) {
        _reconstruction.cameraInitIndex = newIndex
    }

    QtObject {
        id: m
        property variant currentCameraInit: _reconstruction.tempCameraInit ? _reconstruction.tempCameraInit : root.cameraInit
        property variant viewpoints: currentCameraInit ? currentCameraInit.attribute('viewpoints').value : undefined
        property variant intrinsics: currentCameraInit ? currentCameraInit.attribute('intrinsics').value : undefined
        property bool readOnly: root.readOnly || displayHDR.checked
    }

    property variant parsedIntrinsic
    property int numberOfIntrinsics : m.intrinsics ? m.intrinsics.count : 0

    onNumberOfIntrinsicsChanged: {
        parseIntr()
    }

    function populate_model()
    {
        intrinsicModel.clear()
        for (var intr in parsedIntrinsic) {
            intrinsicModel.appendRow(parsedIntrinsic[intr])
        }
    }

    function parseIntr(){
        parsedIntrinsic = {}

        var currentCameraInitIntrinsics =  m.intrinsics

        //Loop through all intrinsics
        for(var i = 0; i < currentCameraInitIntrinsics.count; i++){
            parsedIntrinsic[i] = {}

            //Loop through all attributes
            for(var j=0; j < currentCameraInitIntrinsics.at(i).value.count; j++){
                var currentAttribute = currentCameraInitIntrinsics.at(i).value.at(j)
                //parsedIntrinsic[i][currentAttribute.label] = {}
                if(currentAttribute.type === "GroupAttribute"){
                    //parsedIntrinsic[i][currentAttribute.label] = currentAttribute
                    for(var k=0; k < currentAttribute.value.count; k++){
                        parsedIntrinsic[i][currentAttribute.label + " " + currentAttribute.value.at(k).label] = currentAttribute.value.at(k)
                        //console.warn(currentAttribute.label + " " + currentAttribute.value.at(k).label)
                    }
                }
                else if(currentAttribute.type === "ListAttribute"){

                }
                else{
                    parsedIntrinsic[i][currentAttribute.label] = currentAttribute
                }
            }
        }
        populate_model()
    }



    headerBar: RowLayout {
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
        sensorDatabase: cameraInit ? Filepath.stringToUrl(cameraInit.attribute("sensorDatabase").value) : ""
        readOnly: _reconstruction.computing
        onUpdateIntrinsicsRequest: _reconstruction.rebuildIntrinsics(cameraInit)
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 4

        GridView {
            id: grid

            Layout.fillWidth: true
            Layout.fillHeight: true

            interactive: !intrinsicsFilterButton.checked

            ScrollBar.vertical: ScrollBar {
                minimumSize: 0.05
                active : !intrinsicsFilterButton.checked
                visible: !intrinsicsFilterButton.checked

            }

            focus: true
            clip: true
            cellWidth: thumbnailSizeSlider.value
            cellHeight: cellWidth
            highlightFollowsCurrentItem: true
            keyNavigationEnabled: true

            // Update grid current item when selected view changes
            Connections {
                target: _reconstruction
                onSelectedViewIdChanged: {
                    var idx = grid.model.find(_reconstruction.selectedViewId, "viewId")
                    if(idx >= 0)
                        grid.currentIndex = idx
                }

            }

            model: SortFilterDelegateModel {
                id: sortedModel
                model: m.viewpoints
                sortRole: "path"
                // TODO: provide filtering on reconstruction status
                filterRole: _reconstruction.sfmReport ? root.filter : ""
                filterValue: root.filterValue
                // in modelData:
                // if(filterRole == roleName)
                //     return _reconstruction.isReconstructed(item.model.object)

                // override modelData to return basename of viewpoint's path for sorting
                function modelData(item, roleName) {
                    if(filterRole == roleName)
                        return _reconstruction.isReconstructed(item.model.object)
                    var value = item.model.object.childAttribute(roleName).value
                    if(roleName == sortRole)
                        return Filepath.basename(value)
                    else
                        return value
                }

                delegate: ImageDelegate {
                    id: imageDelegate

                    viewpoint: object.value
                    width: grid.cellWidth
                    height: grid.cellHeight
                    readOnly: m.readOnly
                    displayViewId: displayViewIdsAction.checked
                    visible: !intrinsicsFilterButton.checked

                    isCurrentItem: GridView.isCurrentItem

                    onWidthChanged: {
                        //console.warn("viewpoint " + object.value.get("intrinsicId").value)
                        //console.warn("viewpoint " + m.intrinsics.at(1).childAttribute("intrinsicId"))
                        //console.warn("viewpoint " + m.intrinsics.at(0).value.at(9).name)

                        //console.warn("viewpoint " + m.intrinsics.at(0))






//                         console.warn("viewpoint2 " + (m.viewpoints?m.viewpoints.value:"pute"))
                       // console.warn("intrin " + m.currentCameraInit.attribute('intrinsics').value.count)
//                        //console.warn(viewpoint.get("poseId").value)
                        //console.warn(_reconstruction.isReconstructed(object))

                    }

                    onIsCurrentItemChanged: {
                        if(isCurrentItem)
                            _reconstruction.selectedViewId = viewpoint.get("viewId").value
                    }

                    onPressed: {
                        grid.currentIndex = DelegateModel.filteredIndex
                        if(mouse.button == Qt.LeftButton)
                            grid.forceActiveFocus()
                    }

                    function sendRemoveRequest()
                    {
                        if(!readOnly)
                            removeImageRequest(object)
                    }

                    onRemoveRequest: sendRemoveRequest()
                    Keys.onDeletePressed: sendRemoveRequest()

                    RowLayout {
                        anchors.top: parent.top
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.margins: 2
                        spacing: 2

                        property bool valid: Qt.isQtObject(object) // object can be evaluated to null at some point during creation/deletion
                        property bool inViews: valid && _reconstruction.sfmReport && _reconstruction.isInViews(object)

                        // Camera Initialization indicator
                        IntrinsicsIndicator {
                            intrinsic: parent.valid ? _reconstruction.getIntrinsic(object) : null
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
                            active: viewpoint && (viewpoint.get("viewId").value == centerViewId)
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
                                property bool reconstructed: _reconstruction.sfmReport && _reconstruction.isReconstructed(model.object)
                                text: reconstructed ? MaterialIcons.videocam : MaterialIcons.videocam_off
                                color: reconstructed ? Colors.green : Colors.red
                                ToolTip.text: "<b>Camera: " + (reconstructed ? "" : "Not ") + "Reconstructed</b>"
                            }
                        }
                    }
                }
            }

            // Keyboard shortcut to change current image group
            Keys.priority: Keys.BeforeItem
            Keys.onPressed: {
                if(event.modifiers & Qt.AltModifier)
                {
                    event.accepted = true
                    if(event.key == Qt.Key_Right)
                        root.changeCurrentIndex(Math.min(root.cameraInits.count - 1, root.currentIndex + 1))
                    else if(event.key == Qt.Key_Left)
                        root.changeCurrentIndex(Math.max(0, root.currentIndex - 1))
                }
            }

            // Explanatory placeholder when no image has been added yet
            Column {
                id: dropImagePlaceholder
                anchors.centerIn: parent
                visible: (m.viewpoints ? m.viewpoints.count == 0 : true) && !intrinsicsFilterButton.checked
                spacing: 4
                Label {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: MaterialIcons.photo_library
                    font.pointSize: 24
                    font.family: MaterialIcons.fontFamily
                }
                Label {
                    text: "Drop Image Files / Folders"
                }
            }
            // Placeholder when the filtered images list is empty
            Column {
                id: noImageImagePlaceholder
                anchors.centerIn: parent
                visible: (m.viewpoints ? m.viewpoints.count != 0 : false) && !dropImagePlaceholder.visible && grid.model.count == 0 && !intrinsicsFilterButton.checked
                spacing: 4
                Label {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: MaterialIcons.filter_none
                    font.pointSize: 24
                    font.family: MaterialIcons.fontFamily
                }
                Label {
                    text: "No images in this filtered view"
                }
            }

            RowLayout{
                anchors.fill: parent
                Layout.fillWidth: true
                Layout.fillHeight: true

                TableView{
                    id : intrinsicTable
                    visible: intrinsicsFilterButton.checked
                    Layout.fillHeight: true
                    Layout.fillWidth: true

                    //Provide width for column
                    //Note no size provided for the last column (bool comp) so it uses its automated size
                    property var columnWidths: [90, 75, 75, 75, 125, 60, 60, 45, 45, 175, 60, 60]
                    columnWidthProvider: function (column) { return columnWidths[column] }

                    model: intrinsicModel

                    delegate: IntrinsicDisplayDelegate{}

                    ScrollBar.horizontal: ScrollBar { id: sb }
                }

                TableModel{
                    id : intrinsicModel

                    TableModelColumn { display: "Id" }
                    TableModelColumn { display: "Initial Focal Length" }
                    TableModelColumn { display: "Focal Length x" }
                    TableModelColumn { display: "Focal Length y" }
                    TableModelColumn { display: "Camera Type" }
                    TableModelColumn { display: "Width" }
                    TableModelColumn { display: "Height" }
                    TableModelColumn { display: "Sensor Width" }
                    TableModelColumn { display: "Sensor Height" }
                    TableModelColumn { display: "Serial Number" }
                    TableModelColumn { display: "Principal Point x" }
                    TableModelColumn { display: "Principal Point y" }
                    TableModelColumn { display: "Locked" }

                }

                //CODE FOR HEADERS
                //UNCOMMENT WHEN COMPATIBLE WITH THE RIGHT QT VERSION

//                HorizontalHeaderView {
//                    id: horizontalHeader
//                    syncView: tableView
//                    anchors.left: tableView.left
//                }
            }

            DropArea {
                id: dropArea
                anchors.fill: parent
                enabled: !m.readOnly && !intrinsicsFilterButton.checked
                keys: ["text/uri-list"]
                // TODO: onEntered: call specific method to filter files based on extension
                onDropped: {
                    var augmentSfm = augmentArea.hovered
                    root.filesDropped(drop, augmentSfm)
                }

                // Background opacifier
                Rectangle {
                    visible: dropArea.containsDrag
                    anchors.fill: parent
                    color: root.palette.window
                    opacity: 0.8
                }

                ColumnLayout {
                    anchors.fill: parent
                    visible: dropArea.containsDrag
                    spacing: 1
                    Label {
                        id: addArea
                        property bool hovered: dropArea.drag.y < height
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        text: "Add Images"
                        font.bold: true
                        background: Rectangle {
                            color: parent.hovered ? parent.palette.highlight : parent.palette.window
                            opacity: 0.8
                            border.color: parent.palette.highlight
                        }
                    }

                    // DropArea overlay
                    Label {
                        id: augmentArea
                        property bool hovered: visible && dropArea.drag.y >= y
                        Layout.fillWidth: true
                        Layout.preferredHeight: parent.height * 0.3
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        text: "Augment Reconstruction"
                        font.bold: true
                        wrapMode: Text.WrapAtWordBoundaryOrAnywhere
                        visible: m.viewpoints ? m.viewpoints.count > 0 : false
                        background: Rectangle {
                            color: parent.hovered ? palette.highlight : palette.window
                            opacity: 0.8
                            border.color: parent.palette.highlight
                        }
                    }
                }
            }
        }

        RowLayout {
            Layout.fillHeight: false
            visible: root.cameraInits.count > 1
            Layout.alignment: Qt.AlignHCenter
            spacing: 2

            ToolButton {
                text: MaterialIcons.navigate_before
                font.family: MaterialIcons.fontFamily
                ToolTip.text: "Previous Group (Alt+Left)"
                ToolTip.visible: hovered
                enabled: nodesCB.currentIndex > 0
                onClicked: nodesCB.decrementCurrentIndex()
            }
            Label { id: groupLabel; text: "Group " }
            ComboBox {
                id: nodesCB
                model: root.cameraInits.count
                implicitWidth: 40
                currentIndex: root.currentIndex
                onActivated: root.changeCurrentIndex(currentIndex)
            }
            Label { text: "/ " + (root.cameraInits.count - 1) }
            ToolButton {
                text: MaterialIcons.navigate_next
                font.family: MaterialIcons.fontFamily
                ToolTip.text: "Next Group (Alt+Right)"
                ToolTip.visible: hovered
                enabled: root.currentIndex < root.cameraInits.count - 1
                onClicked: nodesCB.incrementCurrentIndex()
            }
        }
    }

    footerContent: RowLayout {
        // Images count
        id: footer

        function resetButtons(){
            inputImagesFilterButton.checked = false
            estimatedCamerasFilterButton.checked = false
            nonEstimatedCamerasFilterButton.checked = false
        }

        MaterialToolLabelButton {
            id : inputImagesFilterButton
            Layout.minimumWidth: childrenRect.width
            ToolTip.text: grid.model.count + " Input Images"
            iconText: MaterialIcons.image
            label: (m.viewpoints ? m.viewpoints.count : 0)
            padding: 3

            checkable: true
            checked: true

            onCheckedChanged:{
                if(checked) {
                    root.filter = ""
                    root.filterValue = true
                    estimatedCamerasFilterButton.checked = false
                    nonEstimatedCamerasFilterButton.checked = false
                    intrinsicsFilterButton.checked = false;
                }
            }
        }
        // Estimated cameras count
        MaterialToolLabelButton {
            id : estimatedCamerasFilterButton
            Layout.minimumWidth: childrenRect.width
            ToolTip.text: label + " Estimated Cameras"
            iconText: MaterialIcons.videocam
            label: _reconstruction ? _reconstruction.nbCameras.toString() : "0"
            padding: 3

            enabled: _reconstruction.cameraInit && _reconstruction.nbCameras
            checkable: true
            checked: false

            onCheckedChanged:{
                if(checked) {
                    root.filter = "viewId"
                    root.filterValue = true
                    inputImagesFilterButton.checked = false
                    nonEstimatedCamerasFilterButton.checked = false
                    intrinsicsFilterButton.checked = false;
                }
            }
            onEnabledChanged:{
                if(!enabled) {
                    if(checked) inputImagesFilterButton.checked = true;
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
            label: _reconstruction ? ((m.viewpoints ? m.viewpoints.count : 0) - _reconstruction.nbCameras.toString()).toString() : "0"
            padding: 3

            enabled: _reconstruction.cameraInit && _reconstruction.nbCameras
            checkable: true
            checked: false

            onCheckedChanged:{
                if(checked) {
                    filter = "viewId"
                    root.filterValue = false
                    inputImagesFilterButton.checked = false
                    estimatedCamerasFilterButton.checked = false
                    intrinsicsFilterButton.checked = false;
                }
            }
            onEnabledChanged:{
                if(!enabled) {
                    if(checked) inputImagesFilterButton.checked = true;
                    checked = false
                }
            }

        }
        MaterialToolLabelButton {
            id : intrinsicsFilterButton
            Layout.minimumWidth: childrenRect.width
            ToolTip.text: label + " Number of intrinsics"
            iconText: MaterialIcons.camera
            label: _reconstruction ? (m.intrinsics ? m.intrinsics.count : 0) : "0"
            padding: 3


            enabled: m.intrinsics ? m.intrinsics.count > 0 : false
            checkable: true
            checked: false

            onCheckedChanged:{
                if(checked) {
                    inputImagesFilterButton.checked = false
                    estimatedCamerasFilterButton.checked = false
                    nonEstimatedCamerasFilterButton.checked = false
                }
            }
            onEnabledChanged:{
                if(!enabled) {
                    if(checked) inputImagesFilterButton.checked = true;
                    checked = false
                }
            }


        }

        Item { Layout.fillHeight: true; Layout.fillWidth: true }

        MaterialToolLabelButton {
            id: displayHDR
            Layout.minimumWidth: childrenRect.width
            property var activeNode: _reconstruction.activeNodes.get("LdrToHdrMerge").node
            ToolTip.text: "Visualize HDR images: " + (activeNode ? activeNode.label : "No Node")
            iconText: MaterialIcons.filter
            label: activeNode ? activeNode.attribute("nbBrackets").value : ""
            visible: activeNode
            enabled: activeNode && activeNode.isComputed
            property string nodeID: activeNode ? (activeNode.label + activeNode.isComputed) : ""
            onNodeIDChanged: {
                if(checked) {
                    open();
                }
            }
            onEnabledChanged: {
                // Reset the toggle to avoid getting stuck
                // with the HDR node checked but disabled.
                if(checked) {
                    checked = false;
                    close();
                }
            }
            checkable: true
            checked: false
            onClicked: {
                if(checked) {
                    open();
                } else {
                    close();
                }
            }
            function open() {
                if(imageProcessing.checked)
                    imageProcessing.checked = false;
                _reconstruction.setupTempCameraInit(activeNode, "outSfMData");
            }
            function close() {
                    _reconstruction.clearTempCameraInit();
            }
        }

        MaterialToolButton {
            id: imageProcessing
            Layout.minimumWidth: childrenRect.width

            property var activeNode: _reconstruction.activeNodes.get("ImageProcessing").node
            font.pointSize: 15
            padding: 0
            ToolTip.text: "Preprocessed Images: " + (activeNode ? activeNode.label : "No Node")
            text: MaterialIcons.wallpaper
            visible: activeNode && activeNode.attribute("outSfMData").value
            enabled: activeNode && activeNode.isComputed
            property string nodeID: activeNode ? (activeNode.label + activeNode.isComputed) : ""
            onNodeIDChanged: {
                if(checked) {
                    open();
                }
            }
            onEnabledChanged: {
                // Reset the toggle to avoid getting stuck
                // with the HDR node checked but disabled.
                if(checked) {
                    checked = false;
                    close();
                }
            }
            checkable: true
            checked: false
            onClicked: {
                if(checked) {
                    open();
                } else {
                    close();
                }
            }
            function open() {
                if(displayHDR.checked)
                    displayHDR.checked = false;
                _reconstruction.setupTempCameraInit(activeNode, "outSfMData");
            }
            function close() {
                    _reconstruction.clearTempCameraInit();
            }
        }

        Item { Layout.fillHeight: true; width: 1 }

        // Thumbnail size icon and slider
        MaterialToolButton {
            Layout.minimumWidth: childrenRect.width

            text: MaterialIcons.photo_size_select_large
            ToolTip.text: "Thumbnails Scale"
            padding: 0
            anchors.margins: 0
            font.pointSize: 11
            onClicked: { thumbnailSizeSlider.value = defaultCellSize; }
        }
        Slider {
            id: thumbnailSizeSlider
            from: 70
            value: defaultCellSize
            to: 250
            implicitWidth: 70
        }
    }
}
