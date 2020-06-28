import QtQuick 2.7
import QtQuick.Controls 2.0
import QtQuick.Layouts 1.3
import MaterialIcons 2.2
import Controls 1.0

FocusScope {
    id: root

    clip: true

    property url source
    property var metadata
    property var viewIn3D

    property Component floatViewerComp: Qt.createComponent("FloatImage.qml")
    readonly property bool floatViewerAvailable: floatViewerComp.status === Component.Ready
    property alias useFloatImageViewer: displayHDR.checked

    property string loadingModules: {
        if(!imgContainer.image)
            return "";
        var res = "";
        if(imgContainer.image.status === Image.Loading)
            res += " Image";
        if(featuresViewerLoader.status === Loader.Ready)
        {
            for (var i = 0; i < featuresViewerLoader.item.count; ++i) {
                if(featuresViewerLoader.item.itemAt(i).loadingFeatures)
                {
                    res += " Features";
                    break;
                }
            }
        }
        if(msfmDataLoader.status === Loader.Ready)
        {
            if(msfmDataLoader.item.status === MSfMData.Loading)
            {
                res += " SfMData";
            }
        }
        if(mtracksLoader.status === Loader.Ready)
        {
            if(mtracksLoader.item.status === MTracks.Loading)
                res += " Tracks";
        }
        return res;
    }

    function clear()
    {
        source = ''
        metadata = {}
    }

    // slots
    Keys.onPressed: {
        if(event.key == Qt.Key_F) {
            root.fit();
            event.accepted = true;
        }
    }

    // mouse area
    MouseArea {
        anchors.fill: parent
        property double factor: 1.2
        acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.MiddleButton
        onPressed: {
            imgContainer.forceActiveFocus()
            if(mouse.button & Qt.MiddleButton || (mouse.button & Qt.LeftButton && mouse.modifiers & Qt.ShiftModifier))
                drag.target = imgContainer // start drag
        }
        onReleased: {
            drag.target = undefined // stop drag
            if(mouse.button & Qt.RightButton) {
                var menu = contextMenu.createObject(root);
                menu.x = mouse.x;
                menu.y = mouse.y;
                menu.open()
            }
        }
        onWheel: {
            var zoomFactor = wheel.angleDelta.y > 0 ? factor : 1/factor
            if(Math.min(imgContainer.width, imgContainer.image.height) * imgContainer.scale * zoomFactor < 10)
                return
            var point = mapToItem(imgContainer, wheel.x, wheel.y)
            imgContainer.x += (1-zoomFactor) * point.x * imgContainer.scale
            imgContainer.y += (1-zoomFactor) * point.y * imgContainer.scale
            imgContainer.scale *= zoomFactor
        }
    }

    // functions
    function fit() {
        if(imgContainer.image.status != Image.Ready)
            return;
        imgContainer.scale = Math.min(imgLayout.width / imgContainer.image.width, root.height / imgContainer.image.height)
        imgContainer.x = Math.max((imgLayout.width - imgContainer.image.width * imgContainer.scale)*0.5, 0)
        imgContainer.y = Math.max((imgLayout.height - imgContainer.image.height * imgContainer.scale)*0.5, 0)
        // console.warn("fit: imgLayout.width: " + imgContainer.scale + ", imgContainer.image.width: " + imgContainer.image.width)
        // console.warn("fit: imgContainer.scale: " + imgContainer.scale + ", x: " + imgContainer.x + ", y: " + imgContainer.y)
    }

    function getImageFile(type) {
        if (type == "image") {
            return root.source;
        } else if (_reconstruction.depthMap != undefined && _reconstruction.selectedViewId >= 0) {
            return Filepath.stringToUrl(_reconstruction.depthMap.internalFolder+_reconstruction.selectedViewId+"_"+type+"Map.exr");
        }
        return "";
    }

    // context menu
    property Component contextMenu: Menu {
        MenuItem {
            text: "Fit"
            onTriggered: fit()
        }
        MenuItem {
            text: "Zoom 100%"
            onTriggered: {
                imgContainer.scale = 1
                imgContainer.x = Math.max((imgLayout.width-imgContainer.width*imgContainer.scale)*0.5, 0)
                imgContainer.y = Math.max((imgLayout.height-imgContainer.height*imgContainer.scale)*0.5, 0)
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent

        HdrImageToolbar {
            id: hdrImageToolbar
            anchors.margins: 0
            visible: displayImageToolBarAction.checked && displayImageToolBarAction.enabled
            Layout.fillWidth: true
            colorRGBA: {
                if(!floatImageViewerLoader.item ||
                   floatImageViewerLoader.item.status !== Image.Ready)
                {
                    return null;
                }
                if(floatImageViewerLoader.item.containsMouse == false)
                {
                    // console.warn("floatImageViewerLoader: does not contain mouse");
                    return null;
                }
                var pix = floatImageViewerLoader.item.pixelValueAt(Math.floor(floatImageViewerLoader.item.mouseX), Math.floor(floatImageViewerLoader.item.mouseY));
                // console.warn("floatImageViewerLoader: pixel value at (" << floatImageViewerLoader.item.mouseX << "," << floatImageViewerLoader.item.mouseY << "): ", pix);
                return pix;
            }
        }

        // Image
        Item {
            id: imgLayout
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            Image {
                id: alphaBackground
                anchors.fill: parent
                visible: displayAlphaBackground.checked
                fillMode: Image.Tile
                horizontalAlignment: Image.AlignLeft
                verticalAlignment: Image.AlignTop
                source: "../../img/checkerboard_light.png"
                scale: 4
                smooth: false
            }

            Item {
                id: imgContainer
                transformOrigin: Item.TopLeft

                // qtAliceVision Image Viewer
                Loader {
                    id: floatImageViewerLoader
                    active: root.useFloatImageViewer
                    visible: (floatImageViewerLoader.status === Loader.Ready)
                    anchors.centerIn: parent

                    onActiveChanged: {
                        if(active) {
                            // instantiate and initialize a FeaturesViewer component dynamically using Loader.setSource
                            // Note: It does not work to use previously created component, so we re-create it with setSource.
                            // floatViewerComp.createObject(floatImageViewerLoader, {
                            setSource("FloatImage.qml", {
                                'source':  Qt.binding(function() { return getImageFile(imageType.type); }),
                                'gamma': Qt.binding(function() { return hdrImageToolbar.gammaValue; }),
                                'offset': Qt.binding(function() { return hdrImageToolbar.offsetValue; }),
                                'channelModeString': Qt.binding(function() { return hdrImageToolbar.channelModeValue; }),
                            })
                        } else {
                            // Force the unload (instead of using Component.onCompleted to load it once and for all) is necessary since Qt 5.14
                            setSource("", {})
                        }
                    }
                }

                // Simple QML Image Viewer (using Qt or qtOIIO to load images)
                Loader {
                    id: qtImageViewerLoader
                    active: (!root.useFloatImageViewer) || (floatImageViewerLoader.status === Loader.Error)
                    anchors.centerIn: parent
                    sourceComponent: Image {
                        id: qtImageViewer
                        asynchronous: true
                        smooth: false
                        fillMode: Image.PreserveAspectFit
                        autoTransform: true
                        onWidthChanged: if(status==Image.Ready) fit()
                        source: getImageFile(imageType.type)
                        onStatusChanged: {
                            // update cache source when image is loaded
                            if(status === Image.Ready)
                                qtImageViewerCache.source = source
                        }

                        // Image cache of the last loaded image
                        // Only visible when the main one is loading, to keep an image
                        // displayed at all time and smoothen transitions
                        Image {
                            id: qtImageViewerCache

                            anchors.fill: parent
                            asynchronous: true
                            smooth: parent.smooth
                            fillMode: parent.fillMode
                            autoTransform: parent.autoTransform

                            visible: qtImageViewer.status === Image.Loading
                        }
                    }
                }

                property var image: qtImageViewerLoader.active ? qtImageViewerLoader.item : floatImageViewerLoader.item
                width: image ? image.width : 1
                height: image ? image.height : 1
                scale: 1.0

                // FeatureViewer: display view extracted feature points
                // note: requires QtAliceVision plugin - use a Loader to evaluate plugin availability at runtime
                Loader {
                    id: featuresViewerLoader

                    active: displayFeatures.checked

                    // handle rotation/position based on available metadata
                    rotation: {
                        var orientation = metadata ? metadata["Orientation"] : 0
                        switch(orientation) {
                            case "6": return 90;
                            case "8": return -90;
                            default: return 0;
                        }
                    }
                    x: (imgContainer.image && rotation === 90) ? imgContainer.image.paintedWidth : 0
                    y: (imgContainer.image && rotation === -90) ? imgContainer.image.paintedHeight : 0

                    onActiveChanged: {
                        if(active) {
                            // instantiate and initialize a FeaturesViewer component dynamically using Loader.setSource
                            setSource("FeaturesViewer.qml", {
                                'viewId': Qt.binding(function() { return _reconstruction.selectedViewId; }),
                                'model': Qt.binding(function() { return _reconstruction.featureExtraction ? _reconstruction.featureExtraction.attribute("describerTypes").value : ""; }),
                                'featureFolder': Qt.binding(function() { return _reconstruction.featureExtraction ? Filepath.stringToUrl(_reconstruction.featureExtraction.attribute("output").value) : ""; }),
                                'tracks': Qt.binding(function() { return mtracksLoader.status === Loader.Ready ? mtracksLoader.item : null; }),
                                'sfmData': Qt.binding(function() { return msfmDataLoader.status === Loader.Ready ? msfmDataLoader.item : null; }),
                            })
                        } else {
                            // Force the unload (instead of using Component.onCompleted to load it once and for all) is necessary since Qt 5.14
                            setSource("", {})
                        }
                    }
                }

                // FisheyeCircleViewer: display fisheye circle
                // note: use a Loader to evaluate if a PanoramaInit node exist and displayFisheyeCircle checked at runtime
                Loader {
                    anchors.centerIn: parent
                    active: (displayFisheyeCircleLoader.checked && _reconstruction.panoramaInit)

                    // handle rotation/position based on available metadata
                    rotation: {
                        var orientation = metadata ? metadata["Orientation"] : 0
                        switch(orientation) {
                            case "6": return 90;
                            case "8": return -90;
                            default: return 0;
                        }
                    }

                    sourceComponent: CircleGizmo {
                        property bool useAuto: _reconstruction.panoramaInit.attribute("estimateFisheyeCircle").value
                        readOnly: useAuto
                        visible: (!useAuto) || _reconstruction.panoramaInit.isComputed
                        property real userFisheyeRadius: _reconstruction.panoramaInit.attribute("fisheyeRadius").value
                        property variant fisheyeAutoParams: _reconstruction.getAutoFisheyeCircle(_reconstruction.panoramaInit)

                        x: useAuto ? fisheyeAutoParams.x : _reconstruction.panoramaInit.attribute("fisheyeCenterOffset.fisheyeCenterOffset_x").value
                        y: useAuto ? fisheyeAutoParams.y : _reconstruction.panoramaInit.attribute("fisheyeCenterOffset.fisheyeCenterOffset_y").value
                        radius: useAuto ? fisheyeAutoParams.z : ((imgContainer.image ? Math.min(imgContainer.image.width, imgContainer.image.height) : 1.0) * 0.5 * (userFisheyeRadius * 0.01))

                        border.width: Math.max(1, (3.0 / imgContainer.scale))
                        onMoved: {
                            if(!useAuto)
                            {
                                _reconstruction.setAttribute(_reconstruction.panoramaInit.attribute("fisheyeCenterOffset.fisheyeCenterOffset_x"), x)
                                _reconstruction.setAttribute(_reconstruction.panoramaInit.attribute("fisheyeCenterOffset.fisheyeCenterOffset_y"), y)
                            }
                        }
                        onIncrementRadius: {
                            if(!useAuto)
                            {
                                _reconstruction.setAttribute(_reconstruction.panoramaInit.attribute("fisheyeRadius"), _reconstruction.panoramaInit.attribute("fisheyeRadius").value + radiusOffset)
                            }
                        }
                    }
                }
            }

            ColumnLayout {
                anchors.fill: parent
                spacing: 0
                FloatingPane {
                    id: imagePathToolbar
                    Layout.fillWidth: true
                    Layout.fillHeight: false
                    Layout.preferredHeight: childrenRect.height
                    visible: displayImagePathAction.checked

                    RowLayout {
                        width: parent.width
                        height: childrenRect.height

                        // selectable filepath to source image
                        TextField {
                            padding: 0
                            background: Item {}
                            horizontalAlignment: TextInput.AlignLeft
                            Layout.fillWidth: true
                            height: contentHeight
                            font.pointSize: 8
                            readOnly: true
                            selectByMouse: true
                            text: Filepath.urlToString(getImageFile(imageType.type))
                        }

                        // show which depthmap node is active
                        Label {
                            id: depthMapNodeName
                            visible: (_reconstruction.depthMap != undefined) && (imageType.type != "image")
                            text: (_reconstruction.depthMap != undefined ? _reconstruction.depthMap.label : "")
                            font.pointSize: 8

                            horizontalAlignment: TextInput.AlignLeft
                            Layout.fillWidth: false
                            Layout.preferredWidth: contentWidth
                            height: contentHeight
                        }
                    }
                }
                Item {
                    id: imgPlaceholder
                    Layout.fillWidth: true
                    Layout.fillHeight: true

                    // Image Metadata overlay Pane
                    ImageMetadataView {
                        width: 350
                        anchors {
                            top: parent.top
                            right: parent.right
                            bottom: parent.bottom
                        }

                        visible: metadataCB.checked
                        // only load metadata model if visible
                        metadata: visible ? root.metadata : {}
                    }

                    Loader {
                        id: msfmDataLoader
                        // active: _reconstruction.sfm && _reconstruction.sfm.isComputed

                        property bool isUsed: displayFeatures.checked || displaySfmStatsView.checked || displaySfmDataGlobalStats.checked
                        property var activeNode: _reconstruction.sfm
                        property bool isComputed: activeNode && activeNode.isComputed

                        active: false
                        // It takes time to load tracks, so keep them looaded, if we may use it again.
                        // If we load another node, we can trash them (to eventually load the new node data).
                        onIsUsedChanged: {
                            if(!active && isUsed && isComputed)
                                active = true;
                        }
                        onIsComputedChanged: {
                            if(!isComputed)
                                active = false;
                            if(!active && isUsed)
                                active = true;
                        }
                        onActiveNodeChanged: {
                            if(!isUsed)
                                active = false;
                            else if(!isComputed)
                                active = false;
                            else
                                active = true;
                        }

                        Component.onCompleted: {
                            // instantiate and initialize a SfmStatsView component dynamically using Loader.setSource
                            // so it can fail safely if the c++ plugin is not available
                            setSource("MSfMData.qml", {
                                'sfmDataPath': Qt.binding(function() { return Filepath.stringToUrl(isComputed ? activeNode.attribute("output").value : ""); }),
                            })
                        }
                    }
                    Loader {
                        id: mtracksLoader
                        // active: _reconstruction.featureMatching

                        property bool isUsed: displayFeatures.checked || displaySfmStatsView.checked || displaySfmDataGlobalStats.checked
                        property var activeNode: _reconstruction.featureMatching
                        property bool isComputed: activeNode && activeNode.isComputed

                        active: false
                        // It takes time to load tracks, so keep them looaded, if we may use it again.
                        // If we load another node, we can trash them (to eventually load the new node data).
                        onIsUsedChanged: {
                            if(!active && isUsed && isComputed)
                                active = true;
                        }
                        onIsComputedChanged: {
                            if(!isComputed)
                                active = false;
                            if(!active && isUsed)
                                active = true;
                        }
                        onActiveNodeChanged: {
                            if(!isUsed)
                                active = false;
                            else if(!isComputed)
                                active = false;
                            else
                                active = true;
                        }

                        Component.onCompleted: {
                            // instantiate and initialize a SfmStatsView component dynamically using Loader.setSource
                            // so it can fail safely if the c++ plugin is not available
                            setSource("MTracks.qml", {
                                'matchingFolder': Qt.binding(function() { return Filepath.stringToUrl(isComputed ? activeNode.attribute("output").value : ""); }),
                            })
                        }
                    }
                    Loader {
                        id: sfmStatsView
                        anchors.fill: parent
                        active: msfmDataLoader.status === Loader.Ready && displaySfmStatsView.checked

                        Component.onCompleted: {
                            // instantiate and initialize a SfmStatsView component dynamically using Loader.setSource
                            // so it can fail safely if the c++ plugin is not available
                            setSource("SfmStatsView.qml", {
                                'msfmData': Qt.binding(function() { return msfmDataLoader.item; }),
                                'viewId': Qt.binding(function() { return _reconstruction.selectedViewId; }),
                            })
                        }
                    }
                    Loader {
                        id: sfmGlobalStats
                        anchors.fill: parent
                        active: msfmDataLoader.status === Loader.Ready && displaySfmDataGlobalStats.checked

                        Component.onCompleted: {
                            // instantiate and initialize a SfmStatsView component dynamically using Loader.setSource
                            // so it can fail safely if the c++ plugin is not available
                            setSource("SfmGlobalStats.qml", {
                                'msfmData': Qt.binding(function() { return msfmDataLoader.item; }),
                                'mTracks': Qt.binding(function() { return mtracksLoader.item; }),

                            })
                        }
                    }

                    Loader {
                        id: featuresOverlay
                        anchors {
                            bottom: parent.bottom
                            left: parent.left
                            margins: 2
                        }
                        active: displayFeatures.checked && featuresViewerLoader.status === Loader.Ready

                        sourceComponent: FeaturesInfoOverlay {
                            featureExtractionNode: _reconstruction.featureExtraction
                            pluginStatus: featuresViewerLoader.status
                            featuresViewer: featuresViewerLoader.item
                        }
                    }
                }
                FloatingPane {
                    id: bottomToolbar
                    padding: 4
                    Layout.fillWidth: true
                    Layout.preferredHeight: childrenRect.height

                    RowLayout {
                        anchors.fill: parent

                        // zoom label
                        Label {
                            text: ((imgContainer.image && (imgContainer.image.status === Image.Ready)) ? imgContainer.scale.toFixed(2) : "1.00") + "x"
                            state: "xsmall"
                            MouseArea {
                                anchors.fill: parent
                                acceptedButtons: Qt.LeftButton | Qt.RightButton
                                onClicked: {
                                    if(mouse.button & Qt.LeftButton) {
                                        fit()
                                    }
                                    else if(mouse.button & Qt.RightButton) {
                                        var menu = contextMenu.createObject(root);
                                        var point = mapToItem(root, mouse.x, mouse.y)
                                        menu.x = point.x;
                                        menu.y = point.y;
                                        menu.open()
                                    }
                                }
                            }
                        }
                        MaterialToolButton {
                            id: displayAlphaBackground
                            ToolTip.text: "Alpha Background"
                            text: MaterialIcons.texture
                            font.pointSize: 11
                            Layout.minimumWidth: 0
                            checkable: true
                        }
                        MaterialToolButton {
                            id: displayHDR
                            ToolTip.text: "High-Dynamic-Range Image Viewer"
                            text: MaterialIcons.hdr_on
                            // larger font but smaller padding,
                            // so it is visually similar.
                            font.pointSize: 20
                            padding: 0
                            Layout.minimumWidth: 0
                            checkable: true
                            checked: false
                            enabled: root.floatViewerAvailable
                        }
                        MaterialToolButton {
                            id: displayFeatures
                            ToolTip.text: "Display Features"
                            text: MaterialIcons.scatter_plot
                            font.pointSize: 11
                            Layout.minimumWidth: 0
                            checkable: true
                            checked: false
                        }
                        MaterialToolButton {
                            id: displayFisheyeCircleLoader
                            ToolTip.text: "Display Fisheye Circle: " + (_reconstruction.panoramaInit ? _reconstruction.panoramaInit.label : "No Node")
                            text: MaterialIcons.panorama_fish_eye
                            font.pointSize: 11
                            Layout.minimumWidth: 0
                            checkable: true
                            checked: false
                            enabled: _reconstruction.panoramaInit && _reconstruction.panoramaInit.attribute("useFisheye").value
                            visible: _reconstruction.panoramaInit
                        }

                        Label {
                            id: resolutionLabel
                            Layout.fillWidth: true
                            text: imgContainer.image ? (imgContainer.image.sourceSize.width + "x" + imgContainer.image.sourceSize.height) : ""
                            
                            elide: Text.ElideRight
                            horizontalAlignment: Text.AlignHCenter
                            /*Rectangle {
                                anchors.fill: parent
                                color: "blue"
                            }*/
                        }

                        ComboBox {
                            id: imageType
                            // set min size to 5 characters + one margin for the combobox
                            clip: true
                            Layout.minimumWidth: 0
                            Layout.preferredWidth: 6.0 * Qt.application.font.pixelSize
                            flat: true
                            
                            property var types: ["image", "depth", "sim"]
                            property string type: enabled ? types[currentIndex] : types[0]

                            model: types
                            enabled: _reconstruction.depthMap != undefined
                        }

                        MaterialToolButton {
                            enabled: _reconstruction.depthMap != undefined
                            ToolTip.text: "View Depth Map in 3D (" + (_reconstruction.depthMap != undefined ? _reconstruction.depthMap.label : "No DepthMap Node Selected") + ")"
                            text: MaterialIcons.input
                            font.pointSize: 11
                            Layout.minimumWidth: 0

                            onClicked: {
                                root.viewIn3D(root.getImageFile("depth"))
                            }
                        }

                        MaterialToolButton {
                            id: displaySfmStatsView

                            font.family: MaterialIcons.fontFamily
                            text: MaterialIcons.assessment

                            ToolTip.text: "StructureFromMotion Statistics"
                            ToolTip.visible: hovered

                            font.pointSize: 14
                            padding: 2
                            smooth: false
                            flat: true
                            checkable: enabled
                            enabled: _reconstruction.sfm && _reconstruction.sfm.isComputed && _reconstruction.selectedViewId >= 0
                            onCheckedChanged: {
                                if(checked == true)
                                {
                                    displaySfmDataGlobalStats.checked = false
                                    metadataCB.checked = false
                                }
                            }
                        }

                        MaterialToolButton {
                            id: displaySfmDataGlobalStats

                            font.family: MaterialIcons.fontFamily
                            text: MaterialIcons.language

                            ToolTip.text: "StructureFromMotion Global Statistics"
                            ToolTip.visible: hovered

                            font.pointSize: 14
                            padding: 2
                            smooth: false
                            flat: true
                            checkable: enabled
                            enabled: _reconstruction.sfm && _reconstruction.sfm.isComputed
                            onCheckedChanged: {
                                if(checked == true)
                                {
                                    displaySfmStatsView.checked = false
                                    metadataCB.checked = false
                                }
                            }
                        }
                        MaterialToolButton {
                            id: metadataCB

                            font.family: MaterialIcons.fontFamily
                            text: MaterialIcons.info_outline

                            ToolTip.text: "Image Metadata"
                            ToolTip.visible: hovered

                            font.pointSize: 14
                            padding: 2
                            smooth: false
                            flat: true
                            checkable: enabled
                            enabled: _reconstruction.selectedViewId >= 0
                            onCheckedChanged: {
                                if(checked == true)
                                {
                                    displaySfmDataGlobalStats.checked = false
                                    displaySfmStatsView.checked = false
                                }
                            }
                        }

                    }
                }
            }
        }
    }

    // Busy indicator
    BusyIndicator {
        anchors.centerIn: parent
        // running property binding seems broken, only dynamic binding assignment works
        Component.onCompleted: {
            running = Qt.binding(function() { return imgContainer.image && imgContainer.image.status === Image.Loading })
        }
        // disable the visibility when unused to avoid stealing the mouseEvent to the image color picker
        visible: running
    }
}
