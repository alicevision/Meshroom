#include "GLDrawable.hpp"

namespace mockup
{

GLSLPlainColorShader* GLDrawable::_colorUniform(nullptr);
GLSLColoredShader* GLDrawable::_colorArray(nullptr);

void GLDrawable::setShaders(GLSLPlainColorShader* colorUniform, GLSLColoredShader* colorArray)
{
    _colorUniform = colorUniform;
    _colorArray = colorArray;
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

void GLDrawable::setWorldMatrix(const QMatrix4x4& mat)
{
    if(_colorUniform)
        _colorUniform->setWorldMatrix(mat);
    if(_colorArray)
        _colorArray->setWorldMatrix(mat);
}

} // namespace
