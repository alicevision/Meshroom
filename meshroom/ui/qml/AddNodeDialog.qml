import QtQuick 2.9
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3
import Utils 1.0
import MaterialIcons 2.2
import QtQml.Models 2.2

/// Meshroom "Add Node" window
Dialog {
    id: root

    property var node

    x: parent.width / 2 - width / 2
    y: parent.height / 2 - height / 2
    width: 1000

    parent: ApplicationWindow.overlay

    // Fade in transition
    enter: Transition {
        NumberAnimation { property: "opacity"; from: 0.0; to: 1.0 }
    }

    modal: true
    closePolicy: Dialog.CloseOnEscape | Dialog.CloseOnPressOutside
    padding: 30
    topPadding: 25

    header: Pane {
        background: Item {}
        MaterialToolButton {
            text: MaterialIcons.close
            anchors.right: parent.right
            onClicked: root.close()
        }
        Label {
            id:title
            text: "Add Node"
        }
        TextField {
            id: filterTextField
            anchors.top: parent.top
            anchors.horizontalCenter: parent.horizontalCenter
            width: parent.width/2

            Keys.onPressed: grid.unselectAll()
        }
    }
    ColumnLayout {
        width: parent.width
        spacing: 4

        GridView {
            id: grid
            width: parent.width
            height: 600
            
            ScrollBar.vertical: ScrollBar {}
            
            cellWidth: 175
            cellHeight: cellWidth
            
            focus: true
            clip: true
            highlightFollowsCurrentItem: true
            keyNavigationEnabled: true

            function unselectAll() {
                for(var child in grid.contentItem.children) {
                        grid.contentItem.children[child].isCurrentItem = false
                    }
            }

            ListModel {
                id: addNodeIconList

                // "nopreview.png"
                // "No description available"
                // ListElement{file: "";name: ""; info: ""}
                
                ListElement{file: "cameracalibration.png";name: "CameraCalibration"; info: "The internal camera parameters can be calibrated from multiple views of a checkerboard. This allows to retrieve focal length, principal point and distortion parameters."}
                ListElement{file: "nopreview.png";name: "CameraConnection"; info: "No description available"}
                ListElement{file: "nopreview.png";name: "CameraInit"; info: "No description available"}
                ListElement{file: "nopreview.png";name: "CameraLocalization"; info: "No description available"}
                ListElement{file: "nopreview.png";name: "CameraRigCalibration"; info: "No description available"}
                ListElement{file: "nopreview.png";name: "CameraRigLocalization"; info: "No description available"}
                ListElement{file: "nopreview.png";name: "ConvertAnimatedCamera"; info: "No description available"}
                ListElement{file: "nopreview.png";name: "ConvertSfMFormat"; info: "No description available"}
                ListElement{file: "depthmap.jpg";name: "DepthMap"; info: "For all cameras that have been resolved by SfM, we want to retrieve the depth value of each pixel. "}
                ListElement{file: "depthmapfilter.jpg";name: "DepthMapFilter"; info: "To ensure consistency between multiple cameras. A compromise is chosen based on both similarity value and the number of coherent cameras to keep weakly supported surfaces without adding artefacts."}
                ListElement{file: "nopreview.png";name: "ExportAnimatedCamera"; info: "No description available"}
                ListElement{file: "exportmaya.jpg";name: "ExportMaya"; info: "No description available"}
                ListElement{file: "nopreview.png";name: "ExportUndistortedImages"; info: "No description available"}
                ListElement{file: "featureextraction.jpg";name: "FeatureExtraction"; info: "The objective of this step is to extract distinctive groups of pixels that are, to some extent, invariant to changing camera viewpoints during image acquisition. Hence, a feature in the scene should have similar feature descriptions in all images."}
                ListElement{file: "featurematching.jpg";name: "FeatureMatching"; info: "The objective of this step is to match all features between candidate image pairs."}
                ListElement{file: "imagematching.jpg";name: "ImageMatching"; info: "The objective of this part is to find images that are looking to the same areas of the scene. For that, we use the image retrieval techniques to find images that share some content without the cost of resolving all feature matches in details. The ambition is to simplify the image in a compact image descriptor which allows to compute the distance between all images descriptors efficiently."}
                ListElement{file: "nopreview.png";name: "ImageMatchingMultiSfM"; info: "No description available"}
                ListElement{file: "nopreview.png";name: "KeyframeSelection"; info: "No description available"}
                ListElement{file: "meshdecimate.jpg";name: "MeshDecimate"; info: "No description available"}
                ListElement{file: "nopreview.png";name: "MeshDenoising"; info: "No description available"}
                ListElement{file: "meshfiltering.jpg";name: "MeshFiltering"; info: "No description available"}
                ListElement{file: "meshresampling.jpg";name: "MeshResampling"; info: "No description available"}
                ListElement{file: "meshing.jpg";name: "Meshing"; info: "No description available"}
                ListElement{file: "nopreview.png";name: "PrepareDenseScene"; info: "No description available"}
                ListElement{file: "nopreview.png";name: "Publish"; info: "No description available"}
                ListElement{file: "nopreview.png";name: "SfMAlignment"; info: "No description available"}
                ListElement{file: "nopreview.png";name: "SfMTransform"; info: "No description available"}
                ListElement{file: "structurefrommotion.jpg";name: "StructureFromMotion"; info: "The objective of this step is to understand the geometric relationship behind all the observations provided by the input images, and infer the rigid scene structure (3D points) with the pose (position and orientation) and internal calibration of all cameras."}
                ListElement{file: "texturing.jpg";name: "Texturing"; info: "No description available"}
            }

            model: addNodeIconList
            delegate: ImageFrame {path: file; fname: name; description: info; adt: showntext; gridy: grid; doubleclickcreate: bottominteraction.createNode; filtertext: filterTextField}

        }
        Column {
            id: bottominteraction
            topPadding: 0
            function createNode(node)
            {
                root.node(node)
                root.close()
            }

            GroupBox {
                id: description
                width: 450
                title: "Description"
                TextArea {
                    id: showntext
                    property string selectedName: "none"
                    width: parent.width
                    wrapMode: TextEdit.Wrap
                    readOnly: true
                    text: "Select an Item"
                }
            }
            Button {
                text: "Add"
                anchors.left: description.right
                onClicked: bottominteraction.createNode(showntext.selectedName)
            }
        }
    }
}

