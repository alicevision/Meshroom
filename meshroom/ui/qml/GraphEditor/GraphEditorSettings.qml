pragma Singleton
import Qt.labs.settings 1.0


/**
 * Persistent Settings related to the GraphEditor module.
 */
Settings {
    category: 'GraphEditor'
    property bool showAdvancedAttributes: false
    property bool lockOnCompute: true
}
