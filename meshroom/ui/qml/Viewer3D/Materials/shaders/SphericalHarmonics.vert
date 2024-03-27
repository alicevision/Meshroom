#version 450 core

layout(location = 0) in vec3 vertexPosition;
layout(location = 1) in vec3 vertexNormal;

layout(location = 0) out vec3 normal;

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

void main()
{
    normal = vertexNormal;
    gl_Position = mvp * vec4(vertexPosition, 1.0);
}
