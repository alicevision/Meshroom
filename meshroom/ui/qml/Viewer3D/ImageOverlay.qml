import QtQuick 2.12
import QtQuick.Layouts 1.12

/**
 * ImageOverlay enables to display a Viewpoint image on top of a 3D View.
 * It takes the principal point correction into account and handle image ratio to
 * correclty fit or crop according to original image ratio and parent Item ratio.
 */
Item {
    id: root

    /// The url of the image to display
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
        // Preserver aspect fit while display ratio is aligned with image ratio, crop otherwise
        fillMode: width/height >= imageRatio ? Image.PreserveAspectFit : Image.PreserveAspectCrop
        autoTransform: true
    }


    // Custom shader for displaying undistorted images
    // with principal point correction
    ShaderEffect {
        id: shader
        anchors.centerIn: parent
        visible: image.status === Image.Ready
        width: image.paintedWidth
        height: image.paintedHeight
        property variant src: image
        property variant uvCenterOffset

        vertexShader: "
          #version 330 core
          uniform highp mat4 qt_Matrix;
          attribute highp vec4 qt_Vertex;
          attribute highp vec2 qt_MultiTexCoord0;
          out highp vec2 coord;
          void main() {
              coord = qt_MultiTexCoord0;
              gl_Position = qt_Matrix * qt_Vertex;
          }"
        fragmentShader: "
         #version 330 core
          in highp vec2 coord;
          uniform sampler2D src;
          uniform lowp vec2 uvCenterOffset;
          uniform lowp float qt_Opacity;
          out vec4 fragColor;
          void main() {
            vec2 xy = coord + uvCenterOffset;
            fragColor = texture2D(src, xy);
            fragColor.rgb *= qt_Opacity;
            fragColor.a = qt_Opacity;
            // remove undistortion black pixels
            fragColor.a *= step(0.001, fragColor.r + fragColor.g + fragColor.b);
          }"
    }
}
