import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import MaterialIcons 2.2

import "PluginUtils.js" as PluginUtils

/**
 * PluginPublisherLabel shows a plugin's publisher name, 
 * highlighted with a verified icon when the publisher is verified.
 */

RowLayout {
    id: root
    spacing: 3

    property var plugin: null
    readonly property color verifiedColor: '#44AA33'
    readonly property bool isVerified: {
        if (root.plugin === null)
            return false
        if (root.plugin.publisher == null)
            return false
        if (root.plugin.publisher == "meshroomHub")
            return true
        if (PluginUtils.isInstalled(root.plugin) &&
            root.plugin.typeName == "REZ" &&
            !root.plugin.isUserPlugin)
            return true
        return false
    }

    // Publisher Label
    Label {
        text: (root.plugin && root.plugin.publisher) || ""
        elide: Text.ElideRight
        color: root.isVerified ? verifiedColor : palette.windowText
    }

    // Verified Icon
    Label {
        text: MaterialIcons.verified
        font.family: MaterialIcons.fontFamily
        color: verifiedColor
        visible: root.isVerified
    }
}
