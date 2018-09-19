import QtQuick 2.9
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3
import Utils 1.0
import MaterialIcons 2.2
import QtQml.Models 2.2

/// Meshroom "Add Node" window
Dialog {
    id: root

    x: parent.width / 2 - width / 2
    y: parent.height / 2 - height / 2
    width: 600

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
            text: "Add Node"
        }
    }
    ColumnLayout {
        width: parent.width
        spacing: 4

        GridView {
            id: grid
            width: parent.width
            height: 400
            // Layout.fillWidth: true
            // Layout.fillHeight: true
            // flow: GridView.TopToBottom
            
            ScrollBar.vertical: ScrollBar {}
            
            cellWidth: 175
            cellHeight: cellWidth
            
            focus: true
            clip: true
            highlightFollowsCurrentItem: true
            keyNavigationEnabled: true

            ListModel {
                id: addNodeIconList

                ListElement{file: "featureextraction.jpg";name: "FeatureExtraction"; info: "The objective of this step is to extract distinctive groups of pixels that are, to some extent, invariant to changing camera viewpoints during image acquisition. Hence, a feature in the scene should have similar feature descriptions in all images."}
                ListElement{file: "imagematching.jpg";name: "ImageMatching"; info: "The objective of this part is to find images that are looking to the same areas of the scene. For that, we use the image retrieval techniques to find images that share some content without the cost of resolving all feature matches in details. The ambition is to simplify the image in a compact image descriptor which allows to compute the distance between all images descriptors efficiently."}
                ListElement{file: "structurefrommotion.jpg";name: "StructureFromMotion"; info: "The objective of this step is to understand the geometric relationship behind all the observations provided by the input images, and infer the rigid scene structure (3D points) with the pose (position and orientation) and internal calibration of all cameras."}
                ListElement{file: "depthmap.jpg";name: "DepthMap"; info: "For all cameras that have been resolved by SfM, we want to retrieve the depth value of each pixel. "}
                ListElement{file: "depthmapfilter.jpg";name: "DepthMapFilter"; info: "To ensure consistency between multiple cameras. A compromise is chosen based on both similarity value and the number of coherent cameras to keep weakly supported surfaces without adding artefacts."}
            }

            model: addNodeIconList
            delegate: ImageFrame {path: file; fname: name; description: info; adt: showntext; gridy: grid}

        }
        Column {
            id: bottominteraction
            topPadding: 0
            function createNode(node)
            {
                // code
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
                onClicked: createNode(showntext.selectedName)
            }
        }
    }
}

