import Qt3D.Core 2.6
import Qt3D.Render 2.6

import Utils 1.0

Material {
    id: root

    /// Source file containing coefficients
    property url shlSource
    /// Spherical Harmonics coefficients (array of 9 vector3d)
    property var coefficients: noCoeffs
    /// Whether to display normals instead of SH
    property bool displayNormals: false

    // Default coefficients (uniform magenta)
    readonly property var noCoeffs: [
        Qt.vector3d(0.0, 0.0, 0.0),
        Qt.vector3d(0.0, 0.0, 0.0),
        Qt.vector3d(0.0, 0.0, 0.0),
        Qt.vector3d(1.0, 0.0, 1.0),
        Qt.vector3d(0.0, 0.0, 0.0),
        Qt.vector3d(0.0, 0.0, 0.0),
        Qt.vector3d(0.0, 0.0, 0.0),
        Qt.vector3d(0.0, 0.0, 0.0),
        Qt.vector3d(0.0, 0.0, 0.0)
    ]

    effect: SphericalHarmonicsEffect {}

    onShlSourceChanged: {
        if (!shlSource) {
            coefficients = noCoeffs
            return
        }

        Request.get(Filepath.urlToString(shlSource), function(xhr) {
            if (xhr.readyState === XMLHttpRequest.DONE) {
                var coeffs = []
                var lines = xhr.responseText.split("\n")
                lines.forEach(function(l) {
                    var lineCoeffs = []
                    l.split(" ").forEach(function(v) {
                        if (v)
                            lineCoeffs.push(v)
                    })
                    if (lineCoeffs.length == 3)
                        coeffs.push(Qt.vector3d(lineCoeffs[0], lineCoeffs[1], lineCoeffs[2]))
                })

                if (coeffs.length == 9) {
                    coefficients = coeffs
                } else {
                    console.warn("Invalid SHL file: " + shlSource + " with " + coeffs.length + " coefficients.")
                    coefficients = noCoeffs
                }
            }
        })
    }

    parameters: [
        Parameter { name: "shCoeffs[0]"; value: coefficients },
        Parameter { name: "displayNormals"; value: displayNormals }
    ]
}
