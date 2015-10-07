#include "GLSLBackgroundShader.hpp"
#include <QOpenGLBuffer>
#include <iostream>
namespace mockup
{

// TODO : camera ortho
const GLchar* vertex_shader = R"(#version 330 core
        void main(void) {})";

const GLchar* geometry_shader = R"(#version 330 core
    layout(points) in;
    layout(triangle_strip, max_vertices = 4) out;
    const vec2 data[4] = vec2[]
    (
        vec2(-1.0,  1.0),
        vec2(-1.0, -1.0),
        vec2( 1.0,  1.0),
        vec2( 1.0, -1.0)
    );
 
void main() {
  for (int i = 0; i < 4; ++i) {
    gl_Position = vec4( data[i], 0.0, 1.0 );
    EmitVertex();
  }
  EndPrimitive();
}  
    
)";

const GLchar* fragment_shader = R"(#version 330
        layout (location = 0) out vec4 frag_color;
        void main(void) {
            // FIXME: get a relative position
            float col = gl_FragCoord.y/1000;
            frag_color = vec4(col, col, col, 1.0);
        })";

GLSLBackgroundShader::GLSLBackgroundShader()
    : QOpenGLShaderProgram()
{
    addShaderFromSourceCode(QOpenGLShader::Vertex, vertex_shader);
    addShaderFromSourceCode(QOpenGLShader::Geometry, geometry_shader);
    addShaderFromSourceCode(QOpenGLShader::Fragment, fragment_shader);
    link();
    bind();
    _vao.create();
    release();
}

void GLSLBackgroundShader::draw()
{
    glDepthMask(GL_FALSE);
    bind();
    _vao.bind();
    glDrawArrays(GL_POINTS, 0, 1);
    _vao.release();
    release();
    glDepthMask(
        GL_TRUE); // FIXME : this function should restore the previous state of the depth mask
}
}
