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
        if(image.status != Image.Ready)
            return;
        image.scale = Math.min(root.width/image.width, root.height/image.height)
        image.x = Math.max((root.width-image.width*image.scale)*0.5, 0)
        image.y = Math.max((root.height-image.height*image.scale)*0.5, 0)
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
            onTriggered: image.scale = 1
        }
    }

    // Main Image
    Image {
        id: image
        transformOrigin: Item.TopLeft
        asynchronous: true
        smooth: false
        fillMode: Image.PreserveAspectFit
        autoTransform: true
        onWidthChanged: if(status==Image.Ready) fit()
        source: getImageFile(imageType.type)
        onStatusChanged: {
            // update cache source when image is loaded
            if(status === Image.Ready)
                cache.source = source
        }

        // Image cache of the last loaded image
        // Only visible when the main one is loading, to keep an image
        // displayed at all time and smoothen transitions
        Image {
            id: cache

            anchors.fill: parent
            asynchronous: true
            smooth: parent.smooth
            fillMode: parent.fillMode
            autoTransform: parent.autoTransform

            visible: image.status === Image.Loading
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
            x: rotation === 90 ? image.paintedWidth : 0
            y: rotation === -90 ? image.paintedHeight : 0

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
        Component.onCompleted: running = Qt.binding(function() { return image.status === Image.Loading })
    }

    // mouse area
    MouseArea {
        anchors.fill: parent
        property double factor: 1.2
        acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.MiddleButton
        onPressed: {
            image.forceActiveFocus()
            if(mouse.button & Qt.MiddleButton || (mouse.button & Qt.LeftButton && mouse.modifiers & Qt.ShiftModifier))
                drag.target = image // start drag
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
            if(Math.min(image.width*image.scale*zoomFactor, image.height*image.scale*zoomFactor) < 10)
                return
            var point = mapToItem(image, wheel.x, wheel.y)
            image.x += (1-zoomFactor) * point.x * image.scale
            image.y += (1-zoomFactor) * point.y * image.scale
            image.scale *= zoomFactor
        }
    }

    FloatingPane {
        id: topToolbar
        width: parent.width
        height: depthMapNodeName.height+8
        radius: 0
        padding: 4
        // selectable filepath to source image
        TextField {
            width: parent.width-depthMapNodeName.width-5
            padding: 0
            anchors.right: depthMapNodeName.left
            anchors.rightMargin: 5
            background: Item {}
            font.pointSize: 8
            readOnly: true
            selectByMouse: true
            text: Filepath.urlToString(image.source)
        }
        // show which depthmap node is active
        Label {
            id: depthMapNodeName
            text: _reconstruction.depthMap.name
            anchors.right: parent.right
            font.pointSize: 8
            visible: imageType.type != "image"
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
                text: (image.status == Image.Ready ? image.scale.toFixed(2) : "1.00") + "x"
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
                    text: image.sourceSize.width + "x" + image.sourceSize.height
                    anchors.centerIn: parent
                    elide: Text.ElideMiddle
                }
            }

            ComboBox {
                id: imageType
                // set min size to 5 characters + one margin for the combobox
                Layout.minimumWidth: 6.0 * Qt.application.font.pixelSize
                Layout.preferredWidth: Layout.minimumWidth
                // Layout.preferredWidth: 6.0 * Qt.application.font.pixelSize
                // Layout.minimumWidth: 6.0 * Qt.application.font.pixelSize

                property var types: ["image", "depth", "sim"]
                property string type: types[currentIndex]

                model: types
            }

            MaterialToolButton {
                font.pointSize: 11
                enabled: _reconstruction.depthMap != undefined
                ToolTip.text: "View Depth Map in 3D (" + (_reconstruction.depthMap != undefined ? _reconstruction.depthMap.name : "No DepthMap Node Selected") + ")"
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
