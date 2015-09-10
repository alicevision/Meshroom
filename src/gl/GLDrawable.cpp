#include "GLDrawable.hpp"

namespace mockup
{

GLSLPlainColorShader* GLDrawable::_colorUniform(nullptr);
GLSLColoredShader* GLDrawable::_colorArray(nullptr);

QMatrix4x4 GLDrawable::_cameraMatrix;

void GLDrawable::setShaders(GLSLPlainColorShader* colorUniform, GLSLColoredShader* colorArray)
{
    _colorUniform = colorUniform;
    _colorArray = colorArray;
    _cameraMatrix.setToIdentity();
}

void GLDrawable::deleteShaders()
{
    if(_colorUniform)
    {
        delete _colorUniform;
        _colorUniform = nullptr;
    }

    if(_colorArray)
    {
        delete _colorArray;
        _colorArray = nullptr;
    }
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
