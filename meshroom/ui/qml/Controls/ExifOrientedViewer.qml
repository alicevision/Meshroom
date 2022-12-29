import QtQuick 2.11

/**
 * Loader with a predefined transform to orient its content according to the provided Exif tag.
 * Useful when displaying images and overlayed information in the Viewer2D.
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
            angle: {
                switch(orientationTag) {
                    case "3":
                        return 180;
                    case "4":
                        return 180;
                    case "5":
                        return 90;
                    case "6": 
                        return 90;
                    case "7":
                        return -90;
                    case "8": 
                        return -90;
                    default: 
                        return 0;
                }
            }
            origin.x: xOrigin
            origin.y: yOrigin
        }, 
        Scale {
            xScale : {
                switch(orientationTag) {
                    case "2":
                        return -1;
                    case "4":
                        return -1;
                    case "5":
                        return -1;
                    case "7":
                        return -1;
                    default: 
                        return 1;
                }
            }
            origin.x: xOrigin
        }
    ]
}
