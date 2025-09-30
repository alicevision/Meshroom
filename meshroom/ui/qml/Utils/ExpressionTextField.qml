import QtQuick
import QtQuick.Controls

TextField {
    id: root

    // evaluated numeric value (NaN if invalid)
    // It helps keeping the connection that text has so that we don't loose ability to undo/reset
    property bool textChanged: false
    property real evaluatedValue: 0

    property bool hasExprError: false
    property bool isInt: false
    property int decimals: 2

    // Overlay for error state (red border on top of default background)
    Rectangle {
        anchors.fill: parent
        radius: 4
        border.color: "red"
        color: "transparent"
        visible: root.hasExprError
        z: 1
    }

    function raiseError() {
        hasExprError = true
    }

    function clearError() {
        hasExprError = false
    }

    function getEvalExpression(_text) {
        var [_res, _err] = _reconstruction.evaluateMathExpression(_text)
        if (_err == false) {
            if (isInt)
                _res = Math.round(_res)
            else
                _res = _res.toFixed(decimals)
            return _res
        } else {
            console.error("Error: Expression", _text, "is invalid")
            return NaN
        }
    }

    function refreshStatus() {
        if (isNaN(getEvalExpression(root.text))) {
            raiseError()
        } else {
            clearError()
        }
    }

    function updateExpression() {
        var previousEvaluatedValue = evaluatedValue
        var result = getEvalExpression(root.text)
        if (!isNaN(result)) {
            evaluatedValue = result
            clearError()
        } else {
            evaluatedValue = previousEvaluatedValue
            raiseError()
        }
        textChanged = false
    }

    // onAccepted and onEditingFinished will break the bindings to text
    // so if used on fields that needs to be driven by sliders or other qml element,
    // the binding needs to be restored
    // No need to restore the binding if the expression has an error because we don't break it

    onAccepted: {
        if (textChanged)
        {
            updateExpression()
            if (!hasExprError && !isNaN(evaluatedValue)) {
                // Commit the result value to the text field
                if (isInt)
                    root.text = Number(evaluatedValue).toFixed(0)
                else
                    root.text = Number(evaluatedValue).toFixed(decimals)
            }
        }
    }

    onEditingFinished: {
        if (textChanged)
        {
            updateExpression()
            if (!hasExprError && !isNaN(evaluatedValue)) {
                if (isInt)
                    root.text = Number(evaluatedValue).toFixed(0)
                else
                    root.text = Number(evaluatedValue).toFixed(decimals)
            }
        }
    }

    onTextChanged: {
        if (!activeFocus) {
            refreshStatus()
        } else {
            textChanged = true
        }
    }

    Component.onCompleted: {
        refreshStatus()
    }
}
