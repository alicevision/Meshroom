#pragma once

#include <QOpenGLShaderProgram>

#include "GLSLColoredShader.hpp"
#include "GLSLPlainColorShader.hpp"

namespace mockup {


// Allows to have a list of pointers to drawable objects
class GLDrawable
{
public:
    GLDrawable() = default;
    virtual ~GLDrawable() = default;
    virtual void draw() = 0;

    /// SHADER stuff
    // FIXME: I don't think this is a good idea to keep 
    // different shaders as static members of the base class
    // fix would be to think about it and find a solution if needed...
    static void setWorldMatrix(const QMatrix4x4 &);
    static void setShaders(GLSLPlainColorShader *, GLSLColoredShader *);
    static void deleteShaders();

protected:
    static GLSLPlainColorShader *_colorUniform;
    static GLSLColoredShader    *_colorArray;
};


}
