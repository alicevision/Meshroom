.pragma library

/**
 * Analyse raised errors.
 * Works only if errors are written with this specific syntax:
 * [Context] ErrorType: ErrorMessage
 *
 * Maybe it would be better to handle errors on Python side but it should be harder to handle Dialog customization
 */
function analyseError(error) {
    const msg = error.toString()

    // The use of [^] is like . but it takes in count every character including \n (works as a double negation)
    // Group 1: Context
    // Group 2: ErrorType
    // Group 3: ErrorMessage
    const regex = /\[(.*)\]\s(.*):([^]*)/
    if (!regex.test(msg))
        return {
            context: "",
            type: "",
            msg: ""
        }

    const data = regex.exec(msg)

    return {
        context: data[1],
        type: data[2],
        msg: data[3].startsWith("\n") ? data[3].slice(1) : data[3]
    }
}
