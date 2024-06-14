import QtQuick
import Utils 1.0

import AliceVision 1.0 as AliceVision

/**
 * PhongImageViewer displays an Image (albedo + normal) with a given light direction.
 * Shading is done using Blinn-Phong reflection model, material and light direction parameters available.
 * Accept HdrImageToolbar controls (gamma / offset / channel).
 *
 * <!> Requires QtAliceVision plugin.
 */

AliceVision.PhongImageViewer {
    id: root

    width: sourceSize.width
    height: sourceSize.height
    visible: true

    // paintedWidth / paintedHeight / imageStatus for compatibility with standard Image
    property int paintedWidth: sourceSize.width
    property int paintedHeight: sourceSize.height
    property var imageStatus: {
        if (root.status === AliceVision.PhongImageViewer.EStatus.LOADING) {
            return Image.Loading
        } else if (root.status === AliceVision.PhongImageViewer.EStatus.LOADING_ERROR ||
                   root.status === AliceVision.PhongImageViewer.EStatus.MISSING_FILE) {
            return Image.Error
        } else if ((root.sourcePath === "") || (root.sourceSize.height <= 0) || (root.sourceSize.width <= 0)) {
            return Image.Null
        }

        return Image.Ready
    }

    property string channelModeString : "rgba"
    channelMode: {
        switch (channelModeString) {
            case "rgb": return AliceVision.PhongImageViewer.EChannelMode.RGB
            case "r": return AliceVision.PhongImageViewer.EChannelMode.R
            case "g": return AliceVision.PhongImageViewer.EChannelMode.G
            case "b": return AliceVision.PhongImageViewer.EChannelMode.B
            case "a": return AliceVision.PhongImageViewer.EChannelMode.A
            default: return AliceVision.PhongImageViewer.EChannelMode.RGBA
        }
    }
}
