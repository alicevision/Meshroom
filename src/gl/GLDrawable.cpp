#include "GLDrawable.hpp"
#include <QOpenGLBuffer>

namespace meshroom
{

GLSLPlainColorShader* GLDrawable::_colorUniform(nullptr);
GLSLColoredShader* GLDrawable::_colorArray(nullptr);
GLSLBackgroundShader* GLDrawable::_background(nullptr);
QMatrix4x4 GLDrawable::_cameraMatrix;

GLDrawable::GLDrawable(QOpenGLShaderProgram& program)
    : _program(program)
{
}

void GLDrawable::setShaders(GLSLPlainColorShader* colorUniform, GLSLColoredShader* colorArray,
                            GLSLBackgroundShader* background)
{
    _colorUniform = colorUniform;
    _colorArray = colorArray;
    _background = background;
    _cameraMatrix.setToIdentity();
}

void GLDrawable::deleteShaders()
{
    delete _colorUniform;
    delete _colorArray;
    delete _background;
    _colorUniform = nullptr;
    _colorArray = nullptr;
    _background = nullptr;
}

void GLDrawable::uploadShaderMatrix()
{
    QMatrix4x4 mat(_cameraMatrix * _modelMatrix * _transformMatrix);
    // FIXME : subclass QGLProgram so we just have to update the current program
    // instead of updating all programs
    if(_colorUniform)
        _colorUniform->setWorldMatrix(mat);
    if(_colorArray)
        _colorArray->setWorldMatrix(mat);
}

} // namespace
