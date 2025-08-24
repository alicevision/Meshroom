# High-DPI Scaling Implementation for Meshroom

## Overview

This implementation addresses the issue where UI elements appear extremely small on 4K and high-DPI displays, making Meshroom difficult to use effectively.

## Features Implemented

### 1. Automatic DPI Detection
- Detects logical DPI and device pixel ratio from the primary screen
- Automatically calculates appropriate scaling factors
- Supports common scaling scenarios (1x, 1.5x, 2x, 3x, 4x)

### 2. Manual Scaling Controls
- **UI Scale**: Controls the size of buttons, icons, margins, and other UI elements (0.5x to 4.0x)
- **Font Scale**: Independent font scaling for optimal readability (0.5x to 4.0x) 
- **Auto-detect**: Toggle between automatic and manual scaling modes

### 3. Settings Persistence
- Settings stored using Qt's QSettings system
- Preferences persist between application sessions
- Category: "Display" in application settings

### 4. User Interface
- **Settings Dialog**: Accessible via Edit → Display Settings...
- **Real-time Preview**: Shows scaled UI elements before applying
- **Reset to Defaults**: Restores automatic scaling settings
- **Display Information**: Shows current DPI and device characteristics

## Implementation Details

### Core Files Modified/Created:

1. **`meshroom/ui/app.py`**
   - Added Qt high-DPI scaling attributes
   - Implemented DPI detection and automatic scaling calculation
   - Added settings persistence and management methods
   - Exposed scaling properties to QML

2. **`meshroom/ui/qml/Utils/UISettings.qml`**
   - Singleton providing scaling factors to all QML components
   - Helper functions: `dp()` for dimensions, `sp()` for fonts
   - Predefined scaled sizes for common UI elements

3. **`meshroom/ui/qml/DisplaySettingsDialog.qml`**
   - Comprehensive settings dialog with real-time preview
   - DPI information display
   - Manual scaling controls with sliders
   - Preview section showing scaled UI elements

4. **Updated Components:**
   - `Application.qml`: Added settings menu item and updated some font sizes
   - `MaterialToolButton.qml`: Updated to use scaled dimensions and fonts
   - `FloatingPane.qml`: Updated padding and margins to use scaling

### Technical Approach

#### Qt High-DPI Support
```python
# Enabled in MeshroomApp.__init__()
QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
```

#### Scaling Factor Calculation
```python
def _calculateAutoScaleFactor(self):
    dpi = self._dpiInfo["logicalDpi"]
    deviceRatio = self._dpiInfo["devicePixelRatio"]
    baseDpi = 96
    dpiScale = dpi / baseDpi
    autoScale = max(dpiScale, deviceRatio)
    return max(0.5, min(4.0, autoScale))  # Clamp to reasonable range
```

#### QML Usage
```qml
// Using scaled dimensions
Button {
    implicitHeight: UISettings.buttonHeight  // Automatically scaled
    font.pointSize: UISettings.normalFont   // Scaled font
    padding: UISettings.margin              // Scaled spacing
}

// Using helper functions
Rectangle {
    width: UISettings.dp(100)   // 100 * uiScale
    height: UISettings.sp(20)   // 20 * fontScale
}
```

## Benefits

### For Users on 4K/High-DPI Displays:
- **Readable Text**: Fonts automatically scale to appropriate sizes
- **Usable Buttons**: Toolbar buttons and controls are appropriately sized
- **Consistent Experience**: All UI elements scale proportionally
- **Customizable**: Manual fine-tuning available when needed

### For Users on Standard Displays:
- **No Impact**: Scaling defaults to 1.0x on standard DPI displays
- **Backward Compatible**: Existing workflows remain unchanged
- **Optional**: Auto-detection can be disabled for manual control

### For Developers:
- **Minimal Changes**: Existing components work with minimal updates
- **Easy to Use**: Simple `UISettings.dp()` and `UISettings.sp()` functions
- **Consistent API**: Follows existing Meshroom patterns and conventions

## Testing Scenarios

The implementation handles these common display configurations:

| Display Type | Logical DPI | Device Ratio | Auto Scale |
|--------------|-------------|--------------|------------|
| Standard HD  | 96          | 1.0          | 1.0x       |
| High DPI     | 144         | 1.5          | 1.5x       |
| 4K Display   | 192         | 2.0          | 2.0x       |
| Ultra HD     | 288         | 3.0          | 3.0x       |

## Usage Instructions

1. **Automatic Mode** (Default):
   - Application automatically detects display DPI
   - Calculates and applies appropriate scaling
   - No user intervention required

2. **Manual Mode**:
   - Open Edit → Display Settings...
   - Uncheck "Auto-detect display scaling"
   - Adjust UI Scale and Font Scale sliders
   - Preview changes in real-time
   - Click OK to apply

3. **Reset to Defaults**:
   - In Display Settings dialog
   - Click "Restore Defaults" button
   - Restores automatic DPI detection and scaling

This implementation successfully addresses the reported issue #2855 where users experienced tiny text and UI elements on 4K screens, making Meshroom difficult to use effectively.