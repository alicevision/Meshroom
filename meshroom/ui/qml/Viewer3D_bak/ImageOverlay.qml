import QtQuick
import QtQuick.Layouts

/**
 * ImageOverlay enables to display a Viewpoint image on top of a 3D View.
 * It takes the principal point correction into account and handle image ratio to
 * correctly fit or crop according to original image ratio and parent Item ratio.
 */

Item {
    id: root

    /// The URL of the image to display
    property alias source: image.source
    /// Source image ratio
    property real imageRatio: 1.0
    /// Principal Point correction as UV coordinates offset
    property alias uvCenterOffset: shader.uvCenterOffset
    /// Whether to display the frame around the image
    property bool showFrame
    /// Opacity of the image
    property alias imageOpacity: shader.opacity

    implicitWidth: 300
    implicitHeight: 300

    // Display frame
    RowLayout {
        id: frameBG
        spacing: 1
        anchors.fill: parent
        visible: root.showFrame && image.status === Image.Ready
        Rectangle {
            color: "black"
            opacity: 0.5
            Layout.fillWidth: true
            Layout.fillHeight: true
        }
        Item {
            Layout.preferredHeight: image.paintedHeight
            Layout.preferredWidth: image.paintedWidth
        }
        Rectangle {
            color: "black"
            opacity: 0.5
            Layout.fillWidth: true
            Layout.fillHeight: true
        }
    }

    Image {
        id: image
        asynchronous: true
        smooth: false
        anchors.fill: parent
        visible: false
        // Preserve aspect fit while display ratio is aligned with image ratio, crop otherwise
        fillMode: width / height >= imageRatio ? Image.PreserveAspectFit : Image.PreserveAspectCrop
        autoTransform: true
    }


    // Custom shader for displaying undistorted images with principal point correction
    ShaderEffect {
        id: shader
        anchors.centerIn: parent
        visible: image.status === Image.Ready
        width: image.paintedWidth
        height: image.paintedHeight
        property variant src: image
        property variant uvCenterOffset

        fragmentShader: "qrc:/shaders/ImageOverlay.frag.qsb"
    }
}
