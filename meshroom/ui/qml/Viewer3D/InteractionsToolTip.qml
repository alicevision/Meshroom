import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

/**
 * ToolTip listing mouse and keyboard interactions, one titled section per mode.
 * @p interactions is a list of [section, [[input, action], ...]].
 */
ToolTip {
    id: root

    property var interactions: []

    // Cells of a single 2-column grid, so that actions are aligned across sections:
    // {text, kind} with kind "section" (spanning both columns), "input" or "action"
    readonly property var cells: {
        const result = []
        for (let s = 0; s < interactions.length; s++)
        {
            result.push({ "text": interactions[s][0], "kind": "section", "first": s === 0 })
            const rows = interactions[s][1]
            for (let r = 0; r < rows.length; r++)
            {
                result.push({ "text": rows[r][0], "kind": "input" })
                result.push({ "text": rows[r][1], "kind": "action" })
            }
        }
        return result
    }

    contentItem: GridLayout {
        columns: 2
        columnSpacing: 16
        rowSpacing: 1

        Repeater {
            model: root.cells

            Label {
                required property var modelData
                readonly property bool isSection: modelData.kind === "section"

                Layout.columnSpan: isSection ? 2 : 1
                Layout.topMargin: isSection && !modelData.first ? 6 : 0
                Layout.leftMargin: modelData.kind === "input" ? 8 : 0
                text: modelData.text
                font.bold: isSection
                color: modelData.kind === "input" ? palette.highlight : palette.toolTipText
            }
        }
    }
}
