#version 330 core

in vec3 normal;
out vec4 fragColor;

uniform vec3 shCoeffs[9];
uniform bool displayNormals = false;

vec3 resolveSH_Opt(vec3 premulCoefficients[9], vec3 dir)
{
    vec3 result = premulCoefficients[0] * dir.x;
    result += premulCoefficients[1] * dir.y;
    result += premulCoefficients[2] * dir.z;
    result += premulCoefficients[3];
    vec3 dirSq = dir * dir;
    result += premulCoefficients[4] * (dir.x * dir.y);
    result += premulCoefficients[5] * (dir.x * dir.z);
    result += premulCoefficients[6] * (dir.y * dir.z);
    result += premulCoefficients[7] * (dirSq.x - dirSq.y);
    result += premulCoefficients[8] * (3 * dirSq.z - 1);
    return result;
}

void main()
{
    if(displayNormals) {
        // Display normals mode
        fragColor = vec4(normal, 1.0);
    }
    else {
        // Calculate the color from spherical harmonics coeffs
        fragColor = vec4(resolveSH_Opt(shCoeffs, normal), 1.0);
    }
}
