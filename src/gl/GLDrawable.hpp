#pragma once

#include <QOpenGLShaderProgram>
#include "GLSLColoredShader.hpp"
#include "GLSLPlainColorShader.hpp"
#include "GLSLBackgroundShader.hpp"

namespace meshroom
{

class GLDrawable
{
public:
    GLDrawable(QOpenGLShaderProgram& program);
    virtual ~GLDrawable() = default;
    virtual void draw() = 0;

public:
    static void setShaders(GLSLPlainColorShader*, GLSLColoredShader*, GLSLBackgroundShader*);
    static void setCameraMatrix(const QMatrix4x4& mat) { _cameraMatrix = mat; }
    static void deleteShaders();
    void uploadShaderMatrix();
    void setModelMatrix(const QMatrix4x4& mat) { _modelMatrix = mat; }
    void setTransformMatrix(const QMatrix4x4& mat) { _transformMatrix = mat; }
    void setVisibility(const bool& visibility) { _visible = visibility; }
    bool visible() const { return _visible; }

protected:
    QOpenGLShaderProgram& _program;
    static GLSLPlainColorShader* _colorUniform;
    static GLSLColoredShader* _colorArray;
    static GLSLBackgroundShader* _background;
    static QMatrix4x4 _cameraMatrix; // Camera matrix is here in static because it is used in all
                                     // static shaders above
    QMatrix4x4 _modelMatrix;         // Position/orientation matrix of the model
    QMatrix4x4 _transformMatrix;     // Ex: Display scale
    bool _visible = true;
};

} // namespace
