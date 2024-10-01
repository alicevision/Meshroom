pragma Singleton
import QtQuick

/**
 * Singleton that defines utility functions for supporting exif orientation tags.
 *
 * If you are looking for a way to create a Loader that supports exif orientation tags,
 * you can directly use ExifOrientedViewer instead.
 *
 * However if you want to apply an exif orientation tag to another type of QML component,
 * you will need to redefine its transform property using the utility methods given below.
 */
QtObject {

    function rotation(orientationTag) {
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

    function xscale(orientationTag) {
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

}
