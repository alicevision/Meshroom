import QtQuick
import QtQuick.Layouts

LayerListGroup {
    id: root

    property var collection: null

    name: "Meshes"
    emptyText: "No mesh entries"
    layerList: collection ? collection.meshes : null
    showPicking: true

    advancedComponent: Component {
        ColumnLayout {
            id: advanced

            property var entry: null
            readonly property var entryLayer: entry ? entry.layer : null

            spacing: 3

            PropertyComboBox {
                Layout.fillWidth: true
                label: "Shading"
                labelWidth: 70
                model: ["Shaded", "Normal", "Material"]
                target: advanced.entryLayer
                propertyName: "shadingMode"
            }

            PropertyComboBox {
                Layout.fillWidth: true
                label: "Wireframe"
                labelWidth: 70
                model: ["Solid", "Solid + Wireframe", "Wireframe"]
                target: advanced.entryLayer
                propertyName: "wireframeMode"
            }

            PropertySlider {
                Layout.fillWidth: true
                label: "Opacity"
                labelWidth: 70
                from: 0.0
                to: 1.0
                stepSize: 0.01
                defaultValue: 1.0
                target: advanced.entryLayer
                propertyName: "opacity"
            }
        }
    }
}
