#include "GLPointCloud.hpp"
#include "io/AlembicImport.hpp"

#include <QColor>

#include <gl.h>

#include <iostream>
#include <algorithm>
#include <iterator>

namespace meshroom
{

GLPointCloud::GLPointCloud()
    : GLDrawable(*_colorArray)
    , _pointPositions(QOpenGLBuffer::VertexBuffer)
    , _pointColors(QOpenGLBuffer::VertexBuffer)
    , _pointColorsVisibility(QOpenGLBuffer::VertexBuffer)
    , _pointVisibility()
    , _npoints(0)
    , _visibilityThreshold(0) 
    , _maxVisibility(0)
{
    _vertexArrayObject.create();
}

void GLPointCloud::setRawPositions(const void* pointsBuffer, size_t npoints)
{
    // Allow only one load
    if(_npoints != 0)
        return;

    _vertexArrayObject.bind();
    if(_pointPositions.create())
    {
        _pointPositions.setUsagePattern(QOpenGLBuffer::StaticDraw);
        _pointPositions.bind();
        _npoints = npoints;
        _pointPositions.allocate(pointsBuffer, npoints * 3 * sizeof(float));
        glPointSize(1);
        _program.enableAttributeArray("in_position");
        _program.setAttributeBuffer("in_position", GL_FLOAT, 0, 3);
        _pointPositions.release();
        
        {
          //@todo remove me just fake
          _pointVisibility.resize(npoints, 0);
          for(std::size_t i = 0; i < npoints; ++i)
          {
              _pointVisibility[i] = i % 100;
              if(_pointVisibility[i] > _maxVisibility)
                  _maxVisibility = _pointVisibility[i];
          }
          std::cout << "max visibility = " << _maxVisibility << std::endl;
          if(_pointColorsVisibility.create())
          {
              std::vector<float> colors(npoints * 3, 1.0);
              _pointColorsVisibility.setUsagePattern(QOpenGLBuffer::StaticDraw);
              _pointColorsVisibility.bind();
              _pointColorsVisibility.allocate(colors.data(), npoints * 3 * sizeof(float));
              _program.enableAttributeArray("in_color");
              _program.setAttributeBuffer("in_color", GL_FLOAT, 0, 3);
              _pointColorsVisibility.release();
          }
          else
          {
              std::cout << "unable to create buffer for point cloud visibility" << std::endl;
          }
        }
    }
    else
    {
        std::cout << "unable to create buffer for point cloud" << std::endl;
    }
    _vertexArrayObject.release();
}

void GLPointCloud::setRawColors(const void* pointsBuffer, size_t npoints)
{
    _vertexArrayObject.bind();
    if(_pointColors.create())
    {
        _pointColors.setUsagePattern(QOpenGLBuffer::StaticDraw);
        _pointColors.bind();
        _pointColors.allocate(pointsBuffer, npoints * 3 * sizeof(float));
        _program.enableAttributeArray("in_color");
        _program.setAttributeBuffer("in_color", GL_FLOAT, 0, 3);
        _pointColors.release();
    }
    else
    {
        std::cout << "unable to create buffer for point cloud" << std::endl;
    }
    _vertexArrayObject.release();
}

void GLPointCloud::setRawVisibility(const std::vector<std::size_t>& vec_visibility, 
                                    std::size_t npoints)
{
    assert(vec_visibility.size() == npoints);
    
    if(npoints == 0)
    {
        std::cout << "[GLPointCloud::setRawVisibility] no points!" << std::endl;
        return;
    }
    _pointVisibility = vec_visibility;
    
    _maxVisibility = *std::max_element(_pointVisibility.begin(), _pointVisibility.end());
    std::cout << "max visibility = " << _maxVisibility << std::endl;
    
    if(_pointColorsVisibility.create())
    {
        std::vector<float> colors(npoints * 3, 1.0);
        _pointColorsVisibility.setUsagePattern(QOpenGLBuffer::StaticDraw);
        _pointColorsVisibility.bind();
        _pointColorsVisibility.allocate(colors.data(), npoints * 3 * sizeof (float));
        _program.enableAttributeArray("in_color");
        _program.setAttributeBuffer("in_color", GL_FLOAT, 0, 3);
        _pointColorsVisibility.release();
    }
    else
    {
        std::cout << "unable to create buffer for point cloud visibility" << std::endl;
    }

}

void GLPointCloud::draw()
{
    if(_npoints)
    {
        _program.bind();
        _vertexArrayObject.bind();
        glDrawArrays(GL_POINTS, 0, _npoints);
        _vertexArrayObject.release();
        _program.release();
    }
}


void GLPointCloud::setVisibilityThreshold(float threshold)
{
    _visibilityThreshold = (std::size_t) (threshold * _maxVisibility);
    std::cout << "GLPointCloud::_visibilityThreshold = " << _visibilityThreshold << std::endl;
    //@todo recompute colors accordingly
    
    if(_visibilityThreshold > 2 && !_pointVisibility.empty())
    {
      std::vector<float> colors(_npoints * 3, 1.0);
      // for each point
      for(std::size_t i = 0; i < _npoints; ++i)
      {
        // if visibility < _visibilityThreshold
          if(_pointVisibility[i] < _visibilityThreshold)
          {
              // set its color to some grey level
              colors[i*3] = 0.3;
              colors[i*3+1] = 0.3;
              colors[i*3+2] = 0.3;
          }
          else
          {
              assert(_maxVisibility > 0);
              const float normalized = _pointVisibility[i] / float(_maxVisibility);
              // set the color using normalized visibility  (visibility/_maxVisibility)
              // use a HVS ramp HVS(normVisibility, 1.0 ,1.0)
              QColor color;
              color.setHsv((int)(255*normalized), 255, 255);
              colors[i*3] = (float) color.redF();
              colors[i*3+1] = (float) color.greenF();
              colors[i*3+2] = (float) color.blueF();
//              std::cout << "colors[i*3] " << colors[i*3] << "colors[i*3+1] " << colors[i*3+1] << "colors[i*3+2] " << colors[i*3+2] << std::endl;
          }
      }

      glEnable(GL_PROGRAM_POINT_SIZE);
      glPointSize(3.0);
      _vertexArrayObject.bind();
      _pointColorsVisibility.bind();
      _pointColorsVisibility.write(0, colors.data(), _npoints * 3 * sizeof (float));
      _program.enableAttributeArray("in_color");
      _program.setAttributeBuffer("in_color", GL_FLOAT, 0, 3);
      _pointColorsVisibility.release();
      _vertexArrayObject.release();
    }
    else
    {
        glDisable(GL_PROGRAM_POINT_SIZE);
        glPointSize(1.0);
        // use normal colors
        _vertexArrayObject.bind();
        _pointColors.bind();
        _program.enableAttributeArray("in_color");
        _program.setAttributeBuffer("in_color", GL_FLOAT, 0, 3);
        _pointColors.release();
        _vertexArrayObject.release();
    }
}

} // namespace
