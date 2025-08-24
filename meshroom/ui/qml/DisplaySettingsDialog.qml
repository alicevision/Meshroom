import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtCore

import Utils 1.0

Dialog {
    id: root
    title: "Display Settings"
    modal: true
    
    width: 500
    height: 400
    
    anchors.centerIn: parent
    
    standardButtons: Dialog.Ok | Dialog.Cancel | Dialog.RestoreDefaults
    
    property real previewUiScale: UISettings.uiScale
    property real previewFontScale: UISettings.fontScale
    property bool previewAutoDetect: UISettings.autoDetectDpi
    
    onAccepted: {
        UISettings.setUiScale(previewUiScale)
        UISettings.setFontScale(previewFontScale) 
        UISettings.setAutoDetect(previewAutoDetect)
    }
    
    onReset: {
        UISettings.resetToDefaults()
        previewUiScale = UISettings.uiScale
        previewFontScale = UISettings.fontScale
        previewAutoDetect = UISettings.autoDetectDpi
    }
    
    onOpened: {
        // Reset preview values when dialog opens
        previewUiScale = UISettings.uiScale
        previewFontScale = UISettings.fontScale
        previewAutoDetect = UISettings.autoDetectDpi
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: UISettings.margin
        
        // DPI Information
        GroupBox {
            Layout.fillWidth: true
            title: "Display Information"
            
            GridLayout {
                anchors.fill: parent
                columns: 2
                columnSpacing: UISettings.margin
                rowSpacing: UISettings.spacing
                
                Label { text: "Logical DPI:" }
                Label { text: UISettings.dpiInfo.logicalDpi ? UISettings.dpiInfo.logicalDpi.toFixed(1) : "Unknown" }
                
                Label { text: "Device Pixel Ratio:" }
                Label { text: UISettings.dpiInfo.devicePixelRatio ? UISettings.dpiInfo.devicePixelRatio.toFixed(2) : "Unknown" }
                
                Label { text: "High DPI Display:" }
                Label { text: UISettings.dpiInfo.isHighDpi ? "Yes" : "No" }
            }
        }
        
        // Auto-detection setting
        CheckBox {
            id: autoDetectCheck
            Layout.fillWidth: true
            text: "Auto-detect display scaling"
            checked: previewAutoDetect
            onCheckedChanged: previewAutoDetect = checked
            
            ToolTip.visible: hovered
            ToolTip.text: "Automatically adjust UI scaling based on display DPI"
        }
        
        // Manual scaling controls
        GroupBox {
            Layout.fillWidth: true
            title: "Manual Scaling"
            enabled: !previewAutoDetect
            
            GridLayout {
                anchors.fill: parent
                columns: 3
                columnSpacing: UISettings.margin
                rowSpacing: UISettings.spacing
                
                Label { 
                    text: "UI Scale:" 
                    Layout.alignment: Qt.AlignVCenter
                }
                Slider {
                    id: uiScaleSlider
                    Layout.fillWidth: true
                    from: 0.5
                    to: 4.0
                    value: previewUiScale
                    onValueChanged: previewUiScale = value
                    stepSize: 0.1
                    
                    ToolTip {
                        visible: parent.hovered
                        text: "Scale factor for UI elements: " + parent.value.toFixed(1) + "x"
                    }
                }
                Label {
                    text: (previewUiScale * 100).toFixed(0) + "%"
                    Layout.preferredWidth: 50
                }
                
                Label { 
                    text: "Font Scale:" 
                    Layout.alignment: Qt.AlignVCenter
                }
                Slider {
                    id: fontScaleSlider
                    Layout.fillWidth: true
                    from: 0.5
                    to: 4.0
                    value: previewFontScale
                    onValueChanged: previewFontScale = value
                    stepSize: 0.1
                    
                    ToolTip {
                        visible: parent.hovered
                        text: "Scale factor for fonts: " + parent.value.toFixed(1) + "x"
                    }
                }
                Label {
                    text: (previewFontScale * 100).toFixed(0) + "%"
                    Layout.preferredWidth: 50
                }
            }
        }
        
        // Preview section
        GroupBox {
            Layout.fillWidth: true
            title: "Preview"
            
            ColumnLayout {
                anchors.fill: parent
                spacing: UISettings.spacing
                
                Row {
                    spacing: UISettings.dp(8 * previewUiScale)
                    
                    Button {
                        text: "Sample Button"
                        font.pointSize: UISettings.sp(UISettings.normalFont * previewFontScale)
                        implicitHeight: UISettings.dp(32 * previewUiScale)
                    }
                    
                    ToolButton {
                        text: "⚙"
                        font.pointSize: UISettings.sp(UISettings.mediumFont * previewFontScale)
                        implicitWidth: UISettings.dp(28 * previewUiScale)
                        implicitHeight: UISettings.dp(28 * previewUiScale)
                    }
                }
                
                Label {
                    text: "Sample text at different sizes:"
                    font.pointSize: UISettings.sp(UISettings.normalFont * previewFontScale)
                }
                
                Label {
                    text: "• Small text (details)"
                    font.pointSize: UISettings.sp(UISettings.smallFont * previewFontScale)
                }
                
                Label {
                    text: "• Normal text (body)"
                    font.pointSize: UISettings.sp(UISettings.normalFont * previewFontScale)
                }
                
                Label {
                    text: "• Large text (headers)"
                    font.pointSize: UISettings.sp(UISettings.largeFont * previewFontScale)
                }
            }
        }
        
        Item { Layout.fillHeight: true } // Spacer
    }
}