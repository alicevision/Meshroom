#version 450 

#extension GL_NV_fragment_shader_barycentric : require

layout(location = 0) out vec4 fragColor;

void main()
{
    vec3 barycentric = gl_BaryCoordNV;

    float mindist = min(min(barycentric.x, barycentric.y), barycentric.z);

    if (mindist < 0.05)
    {
        fragColor = vec4(1.0, 1.0, 1.0, 1.0);
    }
}
