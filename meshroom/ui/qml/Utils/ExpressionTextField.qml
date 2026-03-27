import QtQuick
import QtQuick.Controls

TextField {
    id: root

    // evaluated numeric value (NaN if invalid)
    // It helps keeping the connection that text has so that we do not lose ability to undo/reset
    property bool exprTextChanged: false
    property real evaluatedValue: 0

    property bool hasExprError: false
    property bool isInt: false

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
        var [_res, _err] = _currentScene.evaluateMathExpression(_text)
        if (_err == false) {
            if (isInt)
                _res = Math.round(_res)
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
        exprTextChanged = false
    }

    // onAccepted and onEditingFinished will break the bindings to text
    // so if used on fields that needs to be driven by sliders or other qml element,
    // the binding needs to be restored
    // No need to restore the binding if the expression has an error because we do not break it

    onAccepted: {
        if (exprTextChanged)
        {
            updateExpression()
            if (!hasExprError && !isNaN(evaluatedValue)) {
                // Commit the result value to the text field
                if (isInt)
                    root.text = Number(evaluatedValue).toFixed(0)
                else
                    root.text = Number(evaluatedValue)
            }
        }
    }

    onEditingFinished: {
        if (exprTextChanged)
        {
            updateExpression()
            if (!hasExprError && !isNaN(evaluatedValue)) {
                if (isInt)
                    root.text = Number(evaluatedValue).toFixed(0)
                else
                    root.text = Number(evaluatedValue)
            }
        }
    }

    onTextChanged: {
        if (!activeFocus && exprTextChanged) {
            refreshStatus()
        } else {
            exprTextChanged = true
        }
    }

    Component.onDestruction: {
        if (exprTextChanged) {
            root.accepted()
        }
    }

    // Increment or decrement the digit immediately to the right of the cursor.
    // The step size is determined by the cursor position relative to the decimal point:
    // - For a cursor before the decimal, the step is the place value of the digit to the right
    //   (e.g. cursor between hundreds and tens → step 10).
    // - For a cursor at or after the decimal, the step is the next decimal place value
    //   (e.g. cursor after one decimal digit → step 0.01).
    // If there is no digit to the right (cursor at end), a new decimal digit is appended.
    function incrementAtCursor(direction) {
        var pos = cursorPosition
        var t = text

        // Find the decimal point position, or use end-of-string as a conceptual decimal position.
        var decimalPos = t.indexOf(".")
        if (decimalPos === -1)
            decimalPos = t.length

        // Compute the exponent that determines the step size.
        var exp
        if (pos <= decimalPos)
            exp = decimalPos - pos - 1
        else
            exp = -(pos - decimalPos)

        // Integer fields never go below a step of 1.
        if (isInt)
            exp = Math.max(0, exp)

        var step = Math.pow(10, exp)

        // Only operate on text that parses as a plain number.
        var value = parseFloat(t)
        if (isNaN(value))
            return

        var newValue = value + direction * step

        // Determine how many decimal places to show in the result.
        var decimals
        if (isInt) {
            decimals = 0
        } else {
            var currentDecimals = (decimalPos < t.length) ? (t.length - decimalPos - 1) : 0
            var stepDecimals = Math.max(0, -exp)
            decimals = Math.max(currentDecimals, stepDecimals)
        }

        var newText = newValue.toFixed(decimals)

        // Compute the cursor position in the new text so it remains right before
        // the digit that was just modified or added.
        var newDecimalPos = newText.indexOf(".")
        if (newDecimalPos === -1)
            newDecimalPos = newText.length

        var newCursor
        if (exp >= 0)
            newCursor = newDecimalPos - exp - 1
        else
            newCursor = newDecimalPos + (-exp)

        newCursor = Math.max(0, Math.min(newText.length, newCursor))

        root.text = newText
        root.cursorPosition = newCursor
        exprTextChanged = true
        updateExpression()
    }

    Keys.onUpPressed: {
        incrementAtCursor(1)
        event.accepted = true
    }

    Keys.onDownPressed: {
        incrementAtCursor(-1)
        event.accepted = true
    }
}
