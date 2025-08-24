pragma Singleton
import QtQuick

/**
 * UISettings singleton provides UI scaling factors and high-DPI support.
 */
Item {
    id: root

    // Scaling factors from the main application
    readonly property real uiScale: MeshroomApp ? MeshroomApp.uiScale : 1.0
    readonly property real fontScale: MeshroomApp ? MeshroomApp.fontScale : 1.0
    readonly property bool autoDetectDpi: MeshroomApp ? MeshroomApp.autoDetectDpi : true
    readonly property var dpiInfo: MeshroomApp ? MeshroomApp.dpiInfo : {}

    // Helper functions for scaled dimensions
    function dp(size) {
        return size * uiScale
    }

    function sp(size) {
        return size * fontScale
    }

    // Commonly used scaled sizes
    readonly property real iconSize: dp(16)
    readonly property real smallIconSize: dp(12)
    readonly property real largeIconSize: dp(24)
    
    readonly property real buttonHeight: dp(32)
    readonly property real toolButtonSize: dp(28)
    
    readonly property real spacing: dp(4)
    readonly property real margin: dp(8)
    readonly property real largeMargin: dp(16)
    
    // Font sizes (in points, will be scaled by Qt)
    readonly property int smallFont: 8
    readonly property int normalFont: 9
    readonly property int mediumFont: 11
    readonly property int largeFont: 12
    readonly property int titleFont: 14
    readonly property int headerFont: 18

    // Methods to set scaling (delegated to main app)
    function setUiScale(scale) {
        if (MeshroomApp) {
            MeshroomApp.setUiScale(scale)
        }
    }

    function setFontScale(scale) {
        if (MeshroomApp) {
            MeshroomApp.setFontScale(scale)
        }
    }

    function setAutoDetect(autoDetect) {
        if (MeshroomApp) {
            MeshroomApp.setAutoDetect(autoDetect)
        }
    }

    function resetToDefaults() {
        if (MeshroomApp) {
            MeshroomApp.resetScalingToDefaults()
        }
    }
}