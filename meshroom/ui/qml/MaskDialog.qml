import QtQuick 2.9
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3
import Utils 1.0
import MaterialIcons 2.2
import Controls 1.0


/// Meshroom "Masking" window
Dialog {
    id: root

    width: parent.width
    height: parent.height

    // Fade in transition
    enter: Transition {
        NumberAnimation { property: "opacity"; from: 0.0; to: 1.0 }
    }

    modal: true
    closePolicy: Dialog.CloseOnEscape
    padding: 30
    topPadding: padding * 2

    property var masking: null
    property string cacheFolder: ""
    property var viewpoints: null
    property int currentIndex: 0
    property var currentViewpoint: viewpoints.isEmpty() ? undefined : viewpoints.at(currentIndex).value
    property string userMarkings: cacheFolder + "/userMarkings.png"
    property string maskFile: cacheFolder + "/" + currentViewpoint.get("viewId").value + ".png"
    property int currentStep: 1

    header: Pane {
        background: Rectangle {
            height: 44
            color: palette.base
        }
        Label {
            text: "Masking"
            anchors.verticalCenter: closeButton.verticalCenter
        }
        MaterialToolButton {
            id: closeButton
            text: MaterialIcons.close
            anchors.right: parent.right
            onClicked: root.close()
        }
    }
    Row {
        width: parent.width
        height: parent.height

        ListView {
            id: viewpointList

            width: parent.width / 6
            height: parent.height
    
            focus: true
            clip: true
            highlightFollowsCurrentItem: true
            keyNavigationEnabled: true
            currentIndex: root.currentIndex 
    
            highlight: Component {
                Rectangle {
                    color: palette.highlight
                    opacity: 0.3
                    z: 2
                }
            }
            highlightMoveDuration: 0
            highlightResizeDuration: 0
    
            ScrollBar.vertical: ScrollBar { 
                active: true
                minimumSize: 0.05 
            }
    
            model: root.viewpoints
            delegate: Rectangle {
                width: parent.width-10
                height: nameLabel.height
                color: Qt.darker(palette.window, 1.15)
                border.color: Qt.darker(palette.highlight)
                border.width: listItemMA.containsMouse ? 2 : 0
                
                MouseArea {
                    id: listItemMA
                    anchors.fill: parent
                    hoverEnabled: true
                    acceptedButtons: Qt.LeftButton
                    onPressed: {
                        root.currentIndex = index
                        root.currentStep = 1
                        paintCanvas.clear()
                    }
    
                    Label { 
                        id: nameLabel
                        text: Filepath.basename(object.value.get("path").value)
                        width: parent.width
                    }
                }
            }
        }

        Column {
            width: parent.width
            height: parent.height - 12

            anchors.left: viewpointList.right
            anchors.right: options.left
            anchors.leftMargin: 30
            anchors.rightMargin: 30

            Image {
                id: img

                // The following ensures that the image width and height is scaled by a known amount
                property bool resizeByWidth: parent.width / sourceSize.width < parent.height / sourceSize.height
                property real scale: resizeByWidth ? parent.width / sourceSize.width : parent.height / sourceSize.height
                width: resizeByWidth ? parent.width : sourceSize.width * scale
                height: resizeByWidth ? sourceSize.height * scale : parent.height

                source: Filepath.stringToUrl(root.currentViewpoint.get("path").value)
                autoTransform: true
                anchors.horizontalCenter: parent.horizontalCenter

                Image {
                    id: maskImg
                    property int number: 0
                    source: Filepath.stringToUrl(root.maskFile) + "?number=" + number
                    opacity: maskOpacity.value
                    cache: false
                    anchors.fill: parent

                    function reload() {
                        // Changing this property will reload the mask
                        number += 1
                    }
                }

                StackLayout {
                    anchors.fill: parent
                    currentIndex: img.status == Image.Ready ? root.currentStep - 1 : 2

                    CropRectangle {
                        id: cropRectangle
                    }

                    PaintCanvas {
                        id: paintCanvas

                        lineWidth: lineWidth.value
                        opacity: canvasOpacity.value
                    }

                    Item {} // If the image is not loaded the overlays will not show
                }
            }
            Row {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: img.bottom
                anchors.margins: 10

                spacing: 6

                MaterialToolButton {
                    id: backButton
                    text: MaterialIcons.arrow_back
                    anchors.left: parent.left
                    onClicked: {
                        if (root.currentIndex > 0) {
                            root.currentIndex -= 1
                            root.currentStep = 1
                            paintCanvas.clear()
                        }
                    }
                }
                // selectable filepath to source image
                TextField {
                    text: Filepath.urlToString(img.source)
                    background: Item {}
                    font.pointSize: 8
                    horizontalAlignment: TextInput.AlignHCenter
                    readOnly: true
                    selectByMouse: true

                    anchors.verticalCenter: forwardButton.verticalCenter
                    anchors.left: backButton.right
                    anchors.right: forwardButton.left
                }
                MaterialToolButton {
                    id: forwardButton
                    text: MaterialIcons.arrow_forward
                    anchors.right: parent.right

                    onClicked: {
                        if (root.currentIndex < root.viewpoints.count-1) {
                            root.currentIndex += 1
                            root.currentStep = 1
                            paintCanvas.clear()
                        }
                    }
                }
            }
        }

        Rectangle {
            id: options
            color: Qt.darker(palette.window, 1.15)
            width: optionsColumn.width
            height: optionsColumn.height
            anchors.right: parent.right

            Column {
                id: optionsColumn
                Layout.fillWidth: true

                RowLayout {
                    MaterialLabel { 
                        text: MaterialIcons.opacity
                        font.family: MaterialIcons.fontFamily
                        ToolTip.text: "Mask Opacity"
                        padding: 2
                    }
                    Slider {
                        id: maskOpacity
                        from: 0
                        to: 1
                        value: 0.5
                    }
                }

                Group {
                    title: "SETTINGS"

                    IntValidator {
                        id: intValidator
                    }

                    GridLayout {
                        width: parent.width
                        columns: 3
                        columnSpacing: 6
                        rowSpacing: 3

                        MaterialLabel { 
                            text: MaterialIcons.photo_size_select_small
                            font.family: MaterialIcons.fontFamily
                            ToolTip.text: "Image Resolution Percentage"
                            padding: 2
                        }
                        Slider {
                            id: resolution
                            from: 10
                            to: 100
                            value: 50
                            stepSize: 1
                            snapMode: Slider.SnapAlways
                        }
                        TextField {
                            text: resolution.value
                            validator: intValidator
                            selectByMouse: true
                            Layout.fillWidth: false

                            onEditingFinished: resolution.value = text
                            onAccepted: focus = false
                            onFocusChanged: {
                                if (focus) {
                                    selectAll()
                                }
                            }
                        }

                        MaterialLabel { 
                            text: MaterialIcons.assessment
                            font.family: MaterialIcons.fontFamily
                            ToolTip.text: "Iterations"
                            padding: 2
                        }
                        Slider {
                            id: iterations
                            from: 1
                            value: 1
                            to: 5
                            stepSize: 1
                            snapMode: Slider.SnapAlways
                        }
                        TextField {
                            text: iterations.value
                            validator: intValidator

                            onEditingFinished: iterations.value = text
                            onAccepted: focus = false
                            onFocusChanged: {
                                if (focus) {
                                    selectAll()
                                }
                            }
                        }
                    }
                }

                Group {
                    title: "STEP 1"
                    width: parent.width
                    labelBackground.color: root.currentStep == 1 ? palette.highlight : palette.base
                    labelBackground.children: MouseArea {
                        anchors.fill: parent

                        onClicked: {
                            root.currentStep = 1
                        }
                    }
                    
                    Column {
                        width: parent.width

                        Label {
                            text: "Move the rectangle so all of the foreground is in it"
                            width: parent.width
                            wrapMode: Label.WordWrap
                        }
                        Button {
                            text: "Compute"
                            enabled: root.currentStep == 1 && img.status == Image.Ready

                            onClicked: {
                                root.masking.rectangle(Filepath.urlToString(img.source), 
                                    [cropRectangle.x, cropRectangle.y, cropRectangle.width, cropRectangle.height],
                                    img.scale,
                                    resolution.value,
                                    iterations.value,
                                    root.maskFile
                                )
                                root.currentStep = 2
                                maskImg.reload()
                            }
                        }
                    }
                }

                Group {
                    title: "STEP 2"
                    width: parent.width
                    labelBackground.color: root.currentStep == 2 ? palette.highlight : palette.base
                    labelBackground.children: MouseArea {
                        anchors.fill: parent

                        onClicked: {
                            root.currentStep = 2
                        }
                    }

                    Column {
                        width: parent.width

                        Label {
                            text: "Draw on foreground marked as background with blue (left mouse button), and background marked as foreground with red (right mouse button)"
                            width: parent.width
                            wrapMode: Label.WordWrap
                        }
                        Button {
                            text: "Clear Canvas"

                            onClicked: {
                                paintCanvas.clear()
                            }
                        } 
                        GridLayout {
                            columns: 2
                            columnSpacing: 6
                            rowSpacing: 3

                            MaterialLabel { 
                                text: MaterialIcons.line_weight
                                font.family: MaterialIcons.fontFamily
                                ToolTip.text: "Line Width"
                                padding: 2
                            }
                            Slider {
                                id: lineWidth
                                from: 1
                                to: 100
                                value: 40
                            }

                            MaterialLabel { 
                                text: MaterialIcons.opacity
                                font.family: MaterialIcons.fontFamily
                                ToolTip.text: "Canvas Opacity"
                                padding: 2
                            }
                            Slider {
                                id: canvasOpacity
                                from: 0
                                to: 1
                                value: 0.5
                            }
                        }
                        Button {
                            text: "Compute"
                            enabled: root.currentStep == 2 && img.status == Image.Ready

                            onClicked: {
                                paintCanvas.save(root.userMarkings)
                                root.masking.markings(Filepath.urlToString(img.source), 
                                    root.userMarkings,
                                    img.scale,
                                    resolution.value,
                                    iterations.value,
                                    root.maskFile
                                )
                                maskImg.reload()
                            }
                        } 
                    }
                }
            }
        }
    }
}
