#pragma once

#include <QOpenGLShaderProgram>
#include "GLSLColoredShader.hpp"
#include "GLSLPlainColorShader.hpp"
#include "GLSLBackgroundShader.hpp"

namespace mockup
{

// Allows to have a list of pointers to drawable objects
class GLDrawable
{
public:
    GLDrawable(QOpenGLShaderProgram &program) : _program(program) {}
    virtual ~GLDrawable() = default;
    virtual void draw() = 0;

    // Sets the camera common to all objects
    void uploadShaderMatrix();
    static void setCameraMatrix(const QMatrix4x4 &);

    /// SHADER stuff
    // FIXME: I don't think this is a good idea to keep
    // different shaders as static members of the base class
    // fix would be to think about it and find a solution if needed...
    static void setShaders(GLSLPlainColorShader *, 
                           GLSLColoredShader *,
                           GLSLBackgroundShader*);
    static void deleteShaders();
   
    /// Sets the model view matrix of the object
    /// its position and orientation
    void setModelMatrix(const QMatrix4x4 &mat) {_modelMatrix = mat;}

protected:
    
    // SHADERS
    QOpenGLShaderProgram& _program; // Shader used in the current object
   
    // Collection of shader, 
    // FIXME: should certainly be moved in a dedicated
    // class 
    static GLSLPlainColorShader *_colorUniform;
    static GLSLColoredShader    *_colorArray;
    static GLSLBackgroundShader *_background;

    // Camera matrix is here in static because it is used in
    // all static shaders above
    static QMatrix4x4           _cameraMatrix;

    // Position/orientation matrix of the model
    QMatrix4x4                  _modelMatrix;

};

} // namespace
