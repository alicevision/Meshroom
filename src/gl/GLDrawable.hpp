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

    static void setWorldMatrix(const QMatrix4x4 &);

    /// SHADER stuff
protected:

    // FIXME: I don't think this is a good idea to keep 
    // different shader as static members of the base class
    // We should think about it ...
    static GLSLPlainColorShader _colorUniform;
    static GLSLColoredShader    _colorArray;
};


}
