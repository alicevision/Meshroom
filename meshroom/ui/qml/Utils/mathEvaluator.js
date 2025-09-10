.pragma library


var symbols = {
    pi: Math.PI,
    e: Math.E,
};

var functions = {
    abs: Math.abs,
    min: Math.min,
    max: Math.max,
    sin: Math.sin,
    cos: Math.cos,
    tan: Math.tan,
    pow: Math.pow,
    sqrt: Math.sqrt,
    exp: Math.exp,
    log: Math.log
};


function removeLeadingZeros(str) {
    return str.replace(/\b0*(\d+(?:\.\d*)?)/g, (match, number) => {
        // If the number starts with a decimal, add a leading zero
        if (number.startsWith('.')) {
            return '0' + number;
        }
        // Otherwise just return the number without leading zeros
        return number;
    });
}


/**
 * Evaluate an expression
 * 
 * @param {*} expr Math expression
 * @returns        float or int
 */
function eval(expr) {
    // Warning : commas are for separating function args and dot to indicate decimals

    // Only allow numbers, operators, parentheses, and function names
    if (!/^[0-9+\-*/^()e.,\s]*$/.test(expr.replace(/\b[a-zA-Z]+\b/g, ""))) {
        throw "Invalid characters in expression";
    }

    expr = removeLeadingZeros(expr);

    // Replace symbols and functions
    for (var symbol in symbols) {
        expr = expr.replace(new RegExp("\\b" + symbol + "\\b", "g"), symbols[symbol]);
    }
    for (var func in functions) {  // Warning : not really a map
        expr = expr.replace(new RegExp("\\b" + func + "\\b", "g"), "Math." + func);
    }

    // Eval with function to avoid issues with undeclared variables
    return Function('"use strict"; return (' + expr + ')')();
}
