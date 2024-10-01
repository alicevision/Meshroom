import QtQuick

import Utils 1.0

/**
 * Loader with a predefined transform to orient its content according to the provided Exif tag.
 * Useful when displaying images and overlaid information in the Viewer2D.
 * 
 * Usage:
 * - set the orientationTag property to specify Exif orientation tag.
 * - set the xOrigin/yOrigin properties to specify the transform origin.
 */
Loader {
    property var orientationTag: undefined

    property real xOrigin: 0
    property real yOrigin: 0

    transform: [
        Rotation {
            angle: ExifOrientation.rotation(orientationTag)
            origin.x: xOrigin
            origin.y: yOrigin
        },
        Scale {
            xScale: ExifOrientation.xscale(orientationTag)
            origin.x: xOrigin
            origin.y: yOrigin
        }
    ]
}
