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

    property bool useFloatImageViewer: false

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

    // functions
    function fit() {
        if(imageViewerWrapper.currentImageViewer.status != Image.Ready)
            return;
        imageViewerWrapper.scale = Math.min(imageViewerWrapper.width/imageViewerWrapper.currentImageViewer.width, imageViewerWrapper.height/imageViewerWrapper.currentImageViewer.height)
        imageViewerWrapper.x = Math.max((imageViewerWrapper.width-imageViewerWrapper.width*imageViewerWrapper.scale)*0.5, 0)
        imageViewerWrapper.y = Math.max((imageViewerWrapper.height-imageViewerWrapper.height*imageViewerWrapper.scale)*0.5, 0)
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
                imageViewerWrapper.scale = 1
                imageViewerWrapper.x = Math.max((imageViewerWrapper.width-imageViewerWrapper.width*imageViewerWrapper.scale)*0.5, 0)
                imageViewerWrapper.y = Math.max((imageViewerWrapper.height-imageViewerWrapper.height*imageViewerWrapper.scale)*0.5, 0)
            }
        }
    }

    // Image
    Item {
        id: imageViewerWrapper
        transformOrigin: Item.TopLeft
        width: parent.width
        height: parent.height

        property var currentImageViewer : qtImageViewerLoader.active ? qtImageViewerLoader.item : floatImageViewerLoader.item

        // qtAliceVision Image Viewer
        Loader {
            id: floatImageViewerLoader
            active: root.useFloatImageViewer
            visible: (floatImageViewerLoader.status === Loader.Ready)
            anchors.centerIn: parent

            Component.onCompleted: {
                // instantiate and initialize a FeaturesViewer component dynamically using Loader.setSource
                setSource("FloatImage.qml", {
                    'source':  Qt.binding(function() { return getImageFile(imageType.type); }),
                    'gamma': Qt.binding(function() { return imageToolbar.gammaValue; }),
                    'offset': Qt.binding(function() { return imageToolbar.offsetValue; }),
                    'channelModeString': Qt.binding(function() { return imageToolbar.channelModeValue; }),
                })
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

        // FeatureViewer: display view extracted feature points
        // note: requires QtAliceVision plugin - use a Loader to evaluate plugin avaibility at runtime
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
            x: (imageViewerWrapper.currentImageViewer && rotation === 90) ? imageViewerWrapper.currentImageViewer.paintedWidth : 0
            y: (imageViewerWrapper.currentImageViewer && rotation === -90) ? imageViewerWrapper.currentImageViewer.paintedHeight : 0

            Component.onCompleted: {
                // instantiate and initialize a FeaturesViewer component dynamically using Loader.setSource
                setSource("FeaturesViewer.qml", {
                    'active':  Qt.binding(function() { return displayFeatures.checked; }),
                    'viewId': Qt.binding(function() { return _reconstruction.selectedViewId; }),
                    'model': Qt.binding(function() { return _reconstruction.featureExtraction.attribute("describerTypes").value; }),
                    'folder': Qt.binding(function() { return Filepath.stringToUrl(_reconstruction.featureExtraction.attribute("output").value); }),
                })
            }
        }
    }

    // Busy indicator
    BusyIndicator {
        anchors.centerIn: parent
        // running property binding seems broken, only dynamic binding assignment works
        Component.onCompleted: {
            running = Qt.binding(function() { return imageViewerWrapper.currentImageViewer && imageViewerWrapper.currentImageViewer.status === Image.Loading })
        }
        // disable the visibility when unused to avoid stealing the mouseEvent to the image color picker
        visible: running
    }

    // mouse area
    MouseArea {
        anchors.fill: parent
        property double factor: 1.2
        acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.MiddleButton
        onPressed: {
            imageViewerWrapper.forceActiveFocus()
            if(mouse.button & Qt.MiddleButton || (mouse.button & Qt.LeftButton && mouse.modifiers & Qt.ShiftModifier))
                drag.target = imageViewerWrapper // start drag
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
            if(Math.min(imageViewerWrapper.width*imageViewerWrapper.scale*zoomFactor, imageViewerWrapper.height*imageViewerWrapper.scale*zoomFactor) < 10)
                return
            var point = mapToItem(imageViewerWrapper, wheel.x, wheel.y)
            imageViewerWrapper.x += (1-zoomFactor) * point.x * imageViewerWrapper.scale
            imageViewerWrapper.y += (1-zoomFactor) * point.y * imageViewerWrapper.scale
            imageViewerWrapper.scale *= zoomFactor
        }
    }

    ColumnLayout {
        id: topToolbar
        anchors.top: parent.top
        anchors.margins: 0
        width: parent.width
        spacing: 0

        ImageToolbar {
            id: imageToolbar
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

        FloatingPane {
            id: imagePathToolbar
            anchors.margins: 0
            radius: 0
            padding: 4
            visible: displayImagePathAction.checked
            Layout.fillWidth: true

            RowLayout {
                anchors.fill: parent

                // selectable filepath to source image
                TextField {
                    padding: 0
                    background: Item {}
                    horizontalAlignment: TextInput.AlignLeft
                    Layout.fillWidth: true
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
                }
            }
        }
    }

    // Image Metadata overlay Pane
    ImageMetadataView {
        width: 350
        anchors {
            top: topToolbar.bottom
            right: parent.right
            bottom: bottomToolbar.top
        }

        visible: metadataCB.checked
        // only load metadata model if visible
        metadata: visible ? root.metadata : {}
    }


    Loader {
        id: featuresOverlay
        anchors.bottom: bottomToolbar.top
        anchors.left: parent.left
        anchors.margins: 2
        active: displayFeatures.checked

        sourceComponent: FeaturesInfoOverlay {
            featureExtractionNode: _reconstruction.featureExtraction
            pluginStatus: featuresViewerLoader.status
            featuresViewer: featuresViewerLoader.item
        }
    }

    FloatingPane {
        id: bottomToolbar
        anchors.bottom: parent.bottom
        anchors.margins: 0
        width: parent.width
        topPadding: 2
        bottomPadding: topPadding

        RowLayout {
            anchors.fill: parent

            // zoom label
            Label {
                text: ((imageViewerWrapper.currentImageViewer && (imageViewerWrapper.currentImageViewer.status == Image.Ready)) ? imageViewerWrapper.scale.toFixed(2) : "1.00") + "x"
                state: "xsmall"
            }
            MaterialToolButton {
                id: displayFeatures
                font.pointSize: 11
                ToolTip.text: "Display Features"
                checkable: true
                text: MaterialIcons.scatter_plot
            }

            Item {
                Layout.fillWidth: true
                Label {
                    id: resolutionLabel
                    text: imageViewerWrapper.currentImageViewer ? (imageViewerWrapper.currentImageViewer.sourceSize.width + "x" + imageViewerWrapper.currentImageViewer.sourceSize.height) : ""
                    anchors.centerIn: parent
                    elide: Text.ElideMiddle
                }
            }

            ComboBox {
                id: imageType
                // set min size to 5 characters + one margin for the combobox
                Layout.minimumWidth: 6.0 * Qt.application.font.pixelSize
                Layout.preferredWidth: Layout.minimumWidth
                flat: true
                
                property var types: ["image", "depth", "sim"]
                property string type: types[currentIndex]

                model: types
                enabled: _reconstruction.depthMap != undefined
            }

            MaterialToolButton {
                font.pointSize: 11
                enabled: _reconstruction.depthMap != undefined
                ToolTip.text: "View Depth Map in 3D (" + (_reconstruction.depthMap != undefined ? _reconstruction.depthMap.label : "No DepthMap Node Selected") + ")"
                text: MaterialIcons.input

                onClicked: {
                    root.viewIn3D(root.getImageFile("depth"))
                }
            }

            ToolButton {
                id: metadataCB
                padding: 3

                font.family: MaterialIcons.fontFamily
                text: MaterialIcons.info_outline

                ToolTip.text: "Image Metadata"
                ToolTip.visible: hovered

                font.pointSize: 12
                smooth: false
                flat: true
                checkable: enabled
            }
        }
    }
}
