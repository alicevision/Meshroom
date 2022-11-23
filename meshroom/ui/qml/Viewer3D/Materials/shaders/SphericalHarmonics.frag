#version 450 core

layout(location = 0) in vec3 normal;
layout(location = 0) out vec4 fragColor;

layout(std140, binding = 0) uniform qt3d_render_view_uniforms {
    mat4 viewMatrix;
    mat4 projectionMatrix;
    mat4 uncorrectedProjectionMatrix;
    mat4 clipCorrectionMatrix;
    mat4 viewProjectionMatrix;
    mat4 inverseViewMatrix;
    mat4 inverseProjectionMatrix;
    mat4 inverseViewProjectionMatrix;
    mat4 viewportMatrix;
    mat4 inverseViewportMatrix;
    vec4 textureTransformMatrix;
    vec3 eyePosition;
    float aspectRatio;
    float gamma;
    float exposure;
    float time;
};
layout(std140, binding = 1) uniform qt3d_command_uniforms {
    mat4 modelMatrix;
    mat4 inverseModelMatrix;
    mat4 modelViewMatrix;
    mat3 modelNormalMatrix;
    mat4 inverseModelViewMatrix;
    mat4 mvp;
    mat4 inverseModelViewProjectionMatrix;
};

layout(std140, binding = 2) uniform input_uniforms {
    vec3 shCoeffs[9];
    bool displayNormals;
};

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
