pragma Singleton
import QtCore

/**
 * Persistent Settings related to the GraphEditor module.
 */

Settings {
    category: 'GraphEditor'
    property bool showAdvancedAttributes: false
    property bool showDefaultAttributes: true
    property bool showModifiedAttributes: true
    property bool showInputAttributes: true
    property bool showOutputAttributes: true
    property bool showLinkAttributes: true
    property bool showNotLinkAttributes: true
    property bool lockOnCompute: true
}
