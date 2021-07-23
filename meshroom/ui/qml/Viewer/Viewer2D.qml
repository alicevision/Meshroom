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
    property alias useFloatImageViewer: displayHDR.checked

    Loader {
        id: aliceVisionPluginLoader
        active: true
        source: "TestAliceVisionPlugin.qml"
    }
    Loader {
        id: oiioPluginLoader
        active: true
        source: "TestOIIOPlugin.qml"
    }
    readonly property bool aliceVisionPluginAvailable: aliceVisionPluginLoader.status === Component.Ready
    readonly property bool oiioPluginAvailable: oiioPluginLoader.status === Component.Ready

    Component.onCompleted: {
        if(!aliceVisionPluginAvailable)
            console.warn("Missing plugin qtAliceVision.")
        if(!oiioPluginAvailable)
            console.warn("Missing plugin qtOIIO.")
    }

    property string loadingModules: {
        if(!imgContainer.image)
            return "";
        var res = "";
        if(imgContainer.image.status === Image.Loading)
            res += " Image";
        if(featuresViewerLoader.status === Loader.Ready && featuresViewerLoader.item)
        {
            for (var i = 0; i < featuresViewerLoader.item.count; ++i) {
                if(featuresViewerLoader.item.itemAt(i).loadingFeatures)
                {
                    res += " Features";
                    break;
                }
            }
        }
        if(mfeaturesLoader.status === Loader.Ready)
        {
            if(mfeaturesLoader.item.status === MFeatures.Loading)
                res += " Features";
        }
        if(mtracksLoader.status === Loader.Ready)
        {
            if(mtracksLoader.item.status === MTracks.Loading)
                res += " Tracks";
        }
        if(msfmDataLoader.status === Loader.Ready)
        {
            if(msfmDataLoader.item.status === MSfMData.Loading)
            {
                res += " SfMData";
            }
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
        if(!_reconstruction.activeNodes)
            return "";
        var depthMapNode = _reconstruction.activeNodes.get('allDepthMap').node;
        if (type == "image") {
            return root.source;
        } else if (depthMapNode != undefined && _reconstruction.selectedViewId >= 0) {
            return Filepath.stringToUrl(depthMapNode.internalFolder+_reconstruction.selectedViewId+"_"+type+"Map.exr");
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
                    active: root.aliceVisionPluginAvailable && root.useFloatImageViewer
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
                                'gain': Qt.binding(function() { return hdrImageToolbar.gainValue; }),
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
                    active: !floatImageViewerLoader.active
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
                        // Only visible when the main one is loading, to maintain a displayed image for smoother transitions
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
                    property var activeNode: _reconstruction.activeNodes.get("FeatureExtraction").node

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
                                'model': Qt.binding(function() { return activeNode ? activeNode.attribute("describerTypes").value : ""; }),
                                'features': Qt.binding(function() { return mfeaturesLoader.status === Loader.Ready ? mfeaturesLoader.item : null; }),
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
                    property var activeNode: _reconstruction.activeNodes.get("PanoramaInit").node
                    active: (displayFisheyeCircleLoader.checked && activeNode)

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
                        property bool useAuto: activeNode.attribute("estimateFisheyeCircle").value
                        readOnly: useAuto
                        visible: (!useAuto) || activeNode.isComputed
                        property real userFisheyeRadius: activeNode.attribute("fisheyeRadius").value
                        property variant fisheyeAutoParams: _reconstruction.getAutoFisheyeCircle(activeNode)

                        x: useAuto ? fisheyeAutoParams.x : activeNode.attribute("fisheyeCenterOffset.fisheyeCenterOffset_x").value
                        y: useAuto ? fisheyeAutoParams.y : activeNode.attribute("fisheyeCenterOffset.fisheyeCenterOffset_y").value
                        radius: useAuto ? fisheyeAutoParams.z : ((imgContainer.image ? Math.min(imgContainer.image.width, imgContainer.image.height) : 1.0) * 0.5 * (userFisheyeRadius * 0.01))

                        border.width: Math.max(1, (3.0 / imgContainer.scale))
                        onMoved: {
                            if(!useAuto)
                            {
                                _reconstruction.setAttribute(activeNode.attribute("fisheyeCenterOffset.fisheyeCenterOffset_x"), x)
                                _reconstruction.setAttribute(activeNode.attribute("fisheyeCenterOffset.fisheyeCenterOffset_y"), y)
                            }
                        }
                        onIncrementRadius: {
                            if(!useAuto)
                            {
                                _reconstruction.setAttribute(activeNode.attribute("fisheyeRadius"), activeNode.attribute("fisheyeRadius").value + radiusOffset)
                            }
                        }
                    }
                }

                // ColorCheckerViewer: display color checker detection results
                // note: use a Loader to evaluate if a ColorCheckerDetection node exist and displayColorChecker checked at runtime
                Loader {
                    id: colorCheckerViewerLoader
                    anchors.centerIn: parent
                    property var activeNode: _reconstruction.activeNodes.get("ColorCheckerDetection").node
                    active: (displayColorCheckerViewerLoader.checked && activeNode)


                    sourceComponent: ColorCheckerViewer {
                        visible: activeNode.isComputed && json !== undefined && imgContainer.image.status === Image.Ready
                        source: Filepath.stringToUrl(activeNode.attribute("outputData").value)
                        image: imgContainer.image
                        viewpoint: _reconstruction.selectedViewpoint
                        zoom: imgContainer.scale

                        updatePane: function() {
                            colorCheckerPane.colors = getColors();
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
                            property var activeNode: root.oiioPluginAvailable ? _reconstruction.activeNodes.get("allDepthMap").node : null
                            visible: (imageType.type != "image") && activeNode
                            text: activeNode ? activeNode.label : ""
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

                    ColorCheckerPane {
                        id: colorCheckerPane
                        width: 250
                        height: 170
                        anchors {
                            top: parent.top
                            right: parent.right
                        }
                        visible: displayColorCheckerViewerLoader.checked && colorCheckerPane.colors !== null
                    }

                    Loader {
                        id: mfeaturesLoader

                        property bool isUsed: displayFeatures.checked
                        property var activeNode: root.aliceVisionPluginAvailable ? _reconstruction.activeNodes.get("FeatureExtraction").node : null
                        property bool isComputed: activeNode && activeNode.isComputed
                        active: false

                        onIsUsedChanged: {
                            active = (!active && isUsed && isComputed);
                        }
                        onIsComputedChanged: {
                            active = (!active && isUsed && isComputed);
                        }
                        onActiveNodeChanged: {
                            active = (!active && isUsed && isComputed);
                        }

                        onActiveChanged: {
                            if(active) {
                                // instantiate and initialize a MFeatures component dynamically using Loader.setSource
                                // so it can fail safely if the c++ plugin is not available
                                setSource("MFeatures.qml", {
                                    'currentViewId': Qt.binding(function() { return _reconstruction.selectedViewId; }),
                                    'describerTypes': Qt.binding(function() { return activeNode ? activeNode.attribute("describerTypes").value : {}; }),
                                    'featureFolder': Qt.binding(function() { return activeNode ? Filepath.stringToUrl(activeNode.attribute("output").value) : ""; }),
                                    'mtracks': Qt.binding(function() { return mtracksLoader.status === Loader.Ready ? mtracksLoader.item : null; }),
                                    'msfmData': Qt.binding(function() { return msfmDataLoader.status === Loader.Ready ? msfmDataLoader.item : null; }),
                                })

                            } else {
                                // Force the unload (instead of using Component.onCompleted to load it once and for all) is necessary since Qt 5.14
                                setSource("", {})
                            }
                        }
                    }
                    Loader {
                        id: msfmDataLoader

                        property bool isUsed: displayFeatures.checked || displaySfmStatsView.checked || displaySfmDataGlobalStats.checked
                        property var activeNode: root.aliceVisionPluginAvailable ? _reconstruction.activeNodes.get('sfm').node : null
                        property bool isComputed: activeNode && activeNode.isComputed
                        property string filepath: Filepath.stringToUrl(isComputed ? activeNode.attribute("output").value : "")

                        active: false
                        // It takes time to load tracks, so keep them looaded, if we may use it again.
                        // If we load another node, we can trash them (to eventually load the new node data).
                        onIsUsedChanged: {
                            if(!active && isUsed && isComputed)
                            {
                                active = true;
                            }
                        }
                        onIsComputedChanged: {
                            if(!isComputed)
                            {
                                active = false;
                            }
                            else if(!active && isUsed)
                            {
                                active = true;
                            }
                        }
                        onActiveNodeChanged: {
                            if(!isUsed)
                            {
                                active = false;
                            }
                            else if(!isComputed)
                            {
                                active = false;
                            }
                            else
                            {
                                active = true;
                            }
                        }

                        onActiveChanged: {
                            if(active) {
                                // instantiate and initialize a SfmStatsView component dynamically using Loader.setSource
                                // so it can fail safely if the c++ plugin is not available
                                setSource("MSfMData.qml", {
                                    'sfmDataPath': Qt.binding(function() { return filepath; }),
                                })
                            } else {
                                // Force the unload (instead of using Component.onCompleted to load it once and for all) is necessary since Qt 5.14
                                setSource("", {})
                            }
                        }
                    }
                    Loader {
                        id: mtracksLoader

                        property bool isUsed: displayFeatures.checked || displaySfmStatsView.checked || displaySfmDataGlobalStats.checked
                        property var activeNode: root.aliceVisionPluginAvailable ? _reconstruction.activeNodes.get('FeatureMatching').node : null
                        property bool isComputed: activeNode && activeNode.isComputed

                        active: false
                        // It takes time to load tracks, so keep them looaded, if we may use it again.
                        // If we load another node, we can trash them (to eventually load the new node data).
                        onIsUsedChanged: {
                            if(!active && isUsed && isComputed) {
                                active = true;
                            }
                        }
                        onIsComputedChanged: {
                            if(!isComputed) {
                                active = false;
                            }
                            else if(!active && isUsed) {
                                active = true;
                            }
                        }
                        onActiveNodeChanged: {
                            if(!isUsed) {
                                active = false;
                            }
                            else if(!isComputed) {
                                active = false;
                            }
                            else {
                                active = true;
                            }
                        }

                        onActiveChanged: {
                            if(active) {
                                // instantiate and initialize a SfmStatsView component dynamically using Loader.setSource
                                // so it can fail safely if the c++ plugin is not available
                                setSource("MTracks.qml", {
                                    'matchingFolder': Qt.binding(function() { return Filepath.stringToUrl(isComputed ? activeNode.attribute("output").value : ""); }),
                                })
                            } else {
                                // Force the unload (instead of using Component.onCompleted to load it once and for all) is necessary since Qt 5.14
                                setSource("", {})
                            }
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
                        active: root.aliceVisionPluginAvailable && displayFeatures.checked && featuresViewerLoader.status === Loader.Ready

                        sourceComponent: FeaturesInfoOverlay {
                            featureExtractionNode: _reconstruction.activeNodes.get('FeatureExtraction').node
                            pluginStatus: featuresViewerLoader.status
                            featuresViewer: featuresViewerLoader.item
                            mfeatures: mfeaturesLoader.item
                        }
                    }

                    Loader {
                        id: ldrHdrCalibrationGraph
                        anchors.fill: parent

                        property var activeNode: _reconstruction.activeNodes.get('LdrToHdrCalibration').node
                        property var isEnabled: displayLdrHdrCalibrationGraph.checked && activeNode && activeNode.isComputed
                        // active: isEnabled
                        // Setting "active" from true to false creates a crash on linux with Qt 5.14.2.
                        // As a workaround, we clear the CameraResponseGraph with an empty node
                        // and hide the loader content.
                        visible: isEnabled

                        sourceComponent: CameraResponseGraph {
                            ldrHdrCalibrationNode: isEnabled ? activeNode : null
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
                        MLabel {
                            text: ((imgContainer.image && (imgContainer.image.status === Image.Ready)) ? imgContainer.scale.toFixed(2) : "1.00") + "x"
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
                            ToolTip.text: "Zoom"
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
                            enabled: root.aliceVisionPluginAvailable
                        }
                        MaterialToolButton {
                            id: displayFeatures
                            ToolTip.text: "Display Features"
                            text: MaterialIcons.scatter_plot
                            font.pointSize: 11
                            Layout.minimumWidth: 0
                            checkable: true
                            checked: false
                            enabled: root.aliceVisionPluginAvailable
                        }
                        MaterialToolButton {
                            id: displayFisheyeCircleLoader
                            property var activeNode: _reconstruction.activeNodes.get('PanoramaInit').node
                            ToolTip.text: "Display Fisheye Circle: " + (activeNode ? activeNode.label : "No Node")
                            text: MaterialIcons.vignette
                            // text: MaterialIcons.panorama_fish_eye
                            font.pointSize: 11
                            Layout.minimumWidth: 0
                            checkable: true
                            checked: false
                            enabled: activeNode && activeNode.attribute("useFisheye").value
                            visible: activeNode
                        }
                        MaterialToolButton {
                            id: displayColorCheckerViewerLoader
                            property var activeNode: _reconstruction.activeNodes.get('ColorCheckerDetection').node
                            ToolTip.text: "Display Color Checker: " + (activeNode ? activeNode.label : "No Node")
                            text: MaterialIcons.view_comfy //view_module grid_on gradient view_comfy border_all
                            font.pointSize: 11
                            Layout.minimumWidth: 0
                            checkable: true
                            enabled: activeNode && activeNode.isComputed && _reconstruction.selectedViewId != -1
                            checked: false
                            visible: activeNode
                            onEnabledChanged: {
                                if(enabled == false)
                                    checked = false
                            }
                            onCheckedChanged: {
                                if(checked == true)
                                {
                                    displaySfmDataGlobalStats.checked = false
                                    displaySfmStatsView.checked = false
                                    metadataCB.checked = false
                                }
                            }
                        }

                        MaterialToolButton {
                            id: displayLdrHdrCalibrationGraph
                            property var activeNode: _reconstruction.activeNodes.get("LdrToHdrCalibration").node
                            property bool isComputed: activeNode && activeNode.isComputed
                            ToolTip.text: "Display Camera Response Function: " + (activeNode ? activeNode.label : "No Node")
                            text: MaterialIcons.timeline
                            font.pointSize: 11
                            Layout.minimumWidth: 0
                            checkable: true
                            checked: false
                            enabled: activeNode && activeNode.isComputed
                            visible: activeNode

                            onIsComputedChanged: {
                                if(!isComputed)
                                    checked = false
                            }
                        }

                        Label {
                            id: resolutionLabel
                            Layout.fillWidth: true
                            text: (imgContainer.image && imgContainer.image.sourceSize.width > 0) ? (imgContainer.image.sourceSize.width + "x" + imgContainer.image.sourceSize.height) : ""
                            
                            elide: Text.ElideRight
                            horizontalAlignment: Text.AlignHCenter
                        }

                        ComboBox {
                            id: imageType
                            property var activeNode: root.oiioPluginAvailable ? _reconstruction.activeNodes.get('allDepthMap').node : null
                            // set min size to 5 characters + one margin for the combobox
                            clip: true
                            Layout.minimumWidth: 0
                            Layout.preferredWidth: 6.0 * Qt.application.font.pixelSize
                            flat: true
                            
                            property var types: ["image", "depth", "sim"]
                            property string type: enabled ? types[currentIndex] : types[0]

                            model: types
                            enabled: activeNode
                        }

                        MaterialToolButton {
                            property var activeNode: root.oiioPluginAvailable ? _reconstruction.activeNodes.get('allDepthMap').node : null
                            enabled: activeNode
                            ToolTip.text: "View Depth Map in 3D (" + (activeNode ? activeNode.label : "No DepthMap Node Selected") + ")"
                            text: MaterialIcons.input
                            font.pointSize: 11
                            Layout.minimumWidth: 0

                            onClicked: {
                                root.viewIn3D(root.getImageFile("depth"))
                            }
                        }

                        MaterialToolButton {
                            id: displaySfmStatsView
                            property var activeNode: root.aliceVisionPluginAvailable ? _reconstruction.activeNodes.get('sfm').node : null

                            font.family: MaterialIcons.fontFamily
                            text: MaterialIcons.assessment

                            ToolTip.text: "StructureFromMotion Statistics"
                            ToolTip.visible: hovered

                            font.pointSize: 14
                            padding: 2
                            smooth: false
                            flat: true
                            checkable: enabled
                            enabled: activeNode && activeNode.isComputed && _reconstruction.selectedViewId >= 0
                            onCheckedChanged: {
                                if(checked == true) {
                                    displaySfmDataGlobalStats.checked = false
                                    metadataCB.checked = false
                                    displayColorCheckerViewerLoader.checked = false
                                }
                            }
                        }

                        MaterialToolButton {
                            id: displaySfmDataGlobalStats
                            property var activeNode: root.aliceVisionPluginAvailable ? _reconstruction.activeNodes.get('sfm').node : null

                            font.family: MaterialIcons.fontFamily
                            text: MaterialIcons.language

                            ToolTip.text: "StructureFromMotion Global Statistics"
                            ToolTip.visible: hovered

                            font.pointSize: 14
                            padding: 2
                            smooth: false
                            flat: true
                            checkable: enabled
                            enabled: activeNode && activeNode.isComputed
                            onCheckedChanged: {
                                if(checked == true) {
                                    displaySfmStatsView.checked = false
                                    metadataCB.checked = false
                                    displayColorCheckerViewerLoader.checked = false
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
                                    displayColorCheckerViewerLoader.checked = false
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
