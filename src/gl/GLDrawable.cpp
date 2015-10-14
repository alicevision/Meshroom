#include "GLDrawable.hpp"
#include <QOpenGLBuffer>

namespace meshroom
{

GLSLPlainColorShader* GLDrawable::_colorUniform(nullptr);
GLSLColoredShader* GLDrawable::_colorArray(nullptr);
GLSLBackgroundShader* GLDrawable::_background(nullptr);

QMatrix4x4 GLDrawable::_cameraMatrix;

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
    _colorUniform = nullptr;

    delete _colorArray;
    _colorArray = nullptr;

    delete _background;
    _background = nullptr;
}

void GLDrawable::uploadShaderMatrix()
{
    QMatrix4x4 mat(_cameraMatrix * _modelMatrix);

    // FIXME : subclass QGLProgram so we just have to update the current program
    // instead of updating all programs
    if(_colorUniform)
        _colorUniform->setWorldMatrix(mat);
    if(_colorArray)
        _colorArray->setWorldMatrix(mat);
}

void GLDrawable::setCameraMatrix(const QMatrix4x4& mat)
{
    _cameraMatrix = mat;
}

} // namespace
