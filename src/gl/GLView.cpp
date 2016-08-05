#include <QQuickWindow>
#include <QPainter>
#include <QBrush>
#include <Eigen/Dense>
#include "GLView.hpp"
#include "GLRenderer.hpp"

namespace meshroom
{

GLView::GLView()
    : _renderer(nullptr)
    , _font(QFont("Helvetica", 10))
    , _camMatTmp(_camera.viewMatrix())
    , _lookAtTmp(_camera.lookAt()) // Stores camera._lookAt locally to avoid recomputing it
    , _showCameras(true)
    , _showGrid(true)
{
    setKeepMouseGrab(true);
    setAcceptedMouseButtons(Qt::AllButtons);
    setFlag(ItemAcceptsInputMethod, true);
    connect(this, SIGNAL(windowChanged(QQuickWindow*)), this,
            SLOT(handleWindowChanged(QQuickWindow*)));
    connect(this, SIGNAL(windowChanged(QQuickWindow*)), this,
            SLOT(handleWindowChanged(QQuickWindow*)));
}

GLView::~GLView()
{
    if(_renderer)
        delete _renderer;
}

bool GLView::showCameras() const
{
    return _showCameras;
}

void GLView::setShowCameras(bool v)
{
    if (v != _showCameras) {
        _showCameras = v;
        if (_renderer)
            _renderer->setShowCameras(v);
        emit showCamerasChanged();
    }
}

bool GLView::showGrid() const
{
    return _showGrid;
}

void GLView::setShowGrid(bool v)
{
    if (v != _showGrid) {
        _showGrid = v;
        if (_renderer)
            _renderer->setShowGrid(v);
        emit showGridChanged();
    }
}

QRect GLView::getSelectionRect() const
{
  QRect rect;
  if (_selectedP0.x() > _selectedP1.x() || (_selectedP0.x() == _selectedP1.x() && _selectedP0.y() > _selectedP1.y()))
    rect = QRect(_selectedP1, _selectedP0);
  else
    rect = QRect(_selectedP0, _selectedP1);
  // When p0==p1, we get a 1x1 rectangle, but we want an empty one.
  return rect.adjusted(0, 0, -1, -1);
}

// Paint selection rectangle/line based on mouse data.
void GLView::paint(QPainter* painter)
{
  painter->setPen(QColor(255, 255, 255));
  painter->setFont(_font);
  painter->drawText(2, 12,
      QString("UP VECTOR: [%1 %2 %3]")
        .arg(_planeNormal[0], 0, 'g', 3)
        .arg(_planeNormal[1], 0, 'g', 3)
        .arg(_planeNormal[2], 0, 'g', 3)
  );
  painter->drawText(2, 24,
      QString("SCALE: %1").arg(_scale, 0, 'g', 3)
  );
  
  painter->setBrush(QBrush(QColor(192, 192, 128, 192)));
  
  if (_selectionMode == RECTANGLE) {
    auto selectedArea = getSelectionRect();
    if (!selectedArea.isEmpty())
      painter->drawRect(selectedArea);
  }
  else {
    painter->drawLine(_selectedP0, _selectedP1);
  }
}

void GLView::setColor(const QColor& color)
{
    if(color == _color)
        return;
    _color = color;
    emit colorChanged();
    refresh();
}

void GLView::handleWindowChanged(QQuickWindow* win)
{
    if(!win)
        return;
    connect(win, SIGNAL(beforeRendering()), this, SLOT(drawgl()), Qt::DirectConnection);
    connect(win, SIGNAL(beforeSynchronizing()), this, SLOT(sync()), Qt::DirectConnection);
    win->setClearBeforeRendering(false);
}

// This function is called from XXXXX
// when the GL context is current
void GLView::sync()
{
    if(!_renderer) // first time
        _renderer = new GLRenderer();

    qreal ratio = window()->devicePixelRatio();
    QPointF pos(x(), y());
    pos = mapToScene(pos);
    _viewport.setX(qRound(ratio * pos.x()));
    _viewport.setY(qRound(ratio * (window()->height() - (pos.y() + height()))));
    _viewport.setWidth(qRound(ratio * width()));
    _viewport.setHeight(qRound(ratio * height()));

    _renderer->setViewport(_viewport);
    _renderer->setClearColor(_color);
    _renderer->setCameraMatrix(_camera.viewMatrix());
    
    // Triggers a load when the file name is not null
    if(!_alembicSceneUrl.isEmpty())
    {
        _renderer->resetScene();
        _renderer->addAlembicScene(_alembicSceneUrl);
        _alembicSceneUrl.clear();
        return;
    }

    if (!_selectedArea.isEmpty()) {
      _renderer->addPointsToSelection(_selectedArea);
      _selectedArea = QRect();
    }
    else if (_clearSelection) {
      _renderer->clearSelection();
      _clearSelection = false;
    }
    _selectedPoints = &_renderer->getSelection();
    
    if (_planeDefined) {
      _renderer->setPlane(_planeNormal, _planeOrigin);
      _planeDefined = false;
    }
    if (_clearPlane) {
      _renderer->clearPlane();
      _clearPlane = false;
    }
}

void GLView::drawgl()
{
    glEnable(GL_SCISSOR_TEST);
    glViewport(_viewport.x(), _viewport.y(), _viewport.width(), _viewport.height());
    glScissor(_viewport.x(), _viewport.y(), _viewport.width(), _viewport.height());

    if(_renderer)
        _renderer->draw();

    glDisable(GL_SCISSOR_TEST);
}

void GLView::refresh()
{
  if(window())
    update();
}

void GLView::loadAlembicScene(const QUrl& url)
{
    // Stores the filename, the load is done later on
    // in the sync function, inside a GL context
    _alembicSceneUrl = url;
    refresh();
}

void GLView::mousePressEvent(QMouseEvent* event)
{
  // Dependending on the combination of key and mouse
  // set the correct mode
  if(event->modifiers() == Qt::AltModifier)
    handleCameraMousePressEvent(event);
  else if (event->modifiers() == Qt::ControlModifier && event->buttons() == Qt::LeftButton)
    handleSelectionMousePressEvent(event);
}

void GLView::mouseMoveEvent(QMouseEvent* event)
{
  if (event->modifiers() == Qt::AltModifier)
    handleCameraMouseMoveEvent(event);
  else if (event->modifiers() == Qt::ControlModifier)
    handleSelectionMouseMoveEvent(event);
}

void GLView::mouseReleaseEvent(QMouseEvent* event)
{
  if (event->modifiers() == Qt::AltModifier)
    _cameraMode = Idle;
  else if (event->modifiers() == Qt::ControlModifier)
    handleSelectionMouseReleaseEvent(event);
  else if (event->modifiers() == Qt::NoModifier && event->button() == Qt::RightButton)
    emit openPopup();
  refresh();
}

void GLView::wheelEvent(QWheelEvent* event)
{
    const int numDegrees = event->delta() / 8;
    const int numSteps = numDegrees / 15;
    const float delta = numSteps * 100;

    float radius = _camera.lookAtRadius();
    translateLineOfSightCamera(_camMatTmp, radius, -delta, 0);

    _camera.setLookAtRadius(radius);
    _camera.setViewMatrix(_camMatTmp);

    _lookAtTmp = _camera.lookAt();
    _mousePos = event->pos();

    refresh();
}

void GLView::handleCameraMousePressEvent(QMouseEvent* event)
{
  _mousePos = event->pos();
  _camMatTmp = _camera.viewMatrix();
  _lookAtTmp = _camera.lookAt();
  switch(event->buttons())
  {
      case Qt::LeftButton:
          _cameraMode = Rotate;
          break;
      case Qt::MidButton:
          _cameraMode = Translate;
          break;
      case Qt::RightButton:
          _cameraMode = Zoom;
          break;
      default:
          break;
  }
}

void GLView::handleCameraMouseMoveEvent(QMouseEvent* event)
{
    switch(_cameraMode)
    {
        case Idle:
            break;
        case Rotate:
        {
            const float dx = _mousePos.x() - event->pos().x(); // TODO divide by canvas size
            const float dy = _mousePos.y() - event->pos().y(); // or unproject ?
            if(0) // TODO select between trackball vs turntable
            {
                trackBallRotateCamera(_camMatTmp, _lookAtTmp, dx, dy);
                _camera.setViewMatrix(_camMatTmp);
                _mousePos = event->pos();
            }
            else // Turntable
            {
                turnTableRotateCamera(_camMatTmp, _lookAtTmp, dx, dy);
                _camera.setViewMatrix(_camMatTmp);
                _mousePos = event->pos();
            }
            refresh();
        }
        break;
        case Translate:
        {
            const float dx = _mousePos.x() - event->pos().x(); // TODO divide by canvas size
            const float dy = _mousePos.y() - event->pos().y(); // or unproject ?
            planeTranslateCamera(_camMatTmp, dx, dy);
            _camera.setViewMatrix(_camMatTmp);
            _lookAtTmp = _camera.lookAt();
            _mousePos = event->pos();
            refresh();
        }
        break;
        case Zoom:
        {
            const float dx = _mousePos.x() - event->pos().x(); // TODO divide by canvas size
            const float dy = _mousePos.y() - event->pos().y(); // or unproject ?
            float radius = _camera.lookAtRadius();
            translateLineOfSightCamera(_camMatTmp, radius, dx, dy);
            _camera.setLookAtRadius(radius);
            _camera.setViewMatrix(_camMatTmp);
            _lookAtTmp = _camera.lookAt();
            _mousePos = event->pos();
            refresh();
        }
        break;
        default:
            break;
    }
}

void GLView::trackBallRotateCamera(QMatrix4x4& cam, const QVector3D& lookAt, float dx, float dy)
{
    QVector3D x(cam.row(0).x(), cam.row(0).y(), cam.row(0).z());
    x.normalize();

    QVector3D y(cam.row(1).x(), cam.row(1).y(), cam.row(1).z());
    y.normalize();

    QQuaternion ry(1, y * dx * 0.005);
    QQuaternion rx(1, -x * dy * 0.005);
    rx.normalize();
    ry.normalize();
    cam.translate(lookAt);
    cam.rotate(rx * ry);
    cam.translate(-lookAt);
}

void GLView::turnTableRotateCamera(QMatrix4x4& cam, const QVector3D& lookAt, float dx, float dy)
{
    QVector3D x(cam.row(0));
    x.normalize();

    QVector3D y(0, 1, 0);
    y.normalize();

    const float sign = cam.row(1).y() > 0 ? 1.f : -1.f;

    QQuaternion ry(1, -y * dx * 0.005 * sign);
    ry.normalize();
    QQuaternion rx(1, -x * dy * 0.005);
    rx.normalize();

    cam.translate(lookAt);
    cam.rotate(rx * ry);
    cam.translate(-lookAt);
}

void GLView::planeTranslateCamera(QMatrix4x4& cam, float dx, float dy)
{
    QVector3D x(cam.row(0));
    x.normalize();

    QVector3D y(cam.row(1));
    y.normalize();

    cam.translate(-x * 0.01 * dx);
    cam.translate(y * 0.01 * dy);
}

void GLView::translateLineOfSightCamera(QMatrix4x4& cam, float& radius, float dx, float dy)
{
    QVector3D z(cam.row(2));
    z.normalize();
    const float offset = 0.01 * (dx + dy);
    cam.translate(-z * offset);
    radius += offset;
}

void GLView::handleSelectionMousePressEvent(QMouseEvent* event)
{
  _mousePos = event->pos();
  _selectedArea = QRect();
  _selectedP0 = _selectedP1 = _mousePos;
}

void GLView::handleSelectionMouseReleaseEvent(QMouseEvent* event)
{
  _selectedArea = getSelectionRect();
  _selectedP0 = _selectedP1 = QPoint();
  if (_selectedArea.isEmpty())
    _clearSelection = true;
  refresh();
}

void GLView::handleSelectionMouseMoveEvent(QMouseEvent* event)
{
  _selectedP1 = event->pos();
  refresh();
}

/////////////////////////////////////////////////////////////////////////////

void GLView::definePlane()
{
  using namespace Eigen;
  
  if (_selectedPoints->size() < 3) {
    qWarning() << "definePlane: must select at least three points";
    return;
  }
  
  MatrixXf mat(3, _selectedPoints->size());
  for (size_t i = 0; i < _selectedPoints->size(); ++i) {
    const auto& p = (*_selectedPoints)[i];
    mat.col(i) = Vector3f(p[0], p[1], p[2]);
  }
  
  // See http://math.stackexchange.com/questions/99299/best-fitting-plane-given-a-set-of-points
  
  // Translate to origin.
  Vector3f origin = mat.rowwise().sum() / mat.cols();
  mat.colwise() -= origin;
  _planeOrigin = QVector3D(origin(0), origin(1), origin(2));
  
  // Calculate SVD. Need only left singular vectors. Singular values are sorted in decreasing order.
  JacobiSVD<MatrixXf> svd(mat, ComputeThinU);
  const auto& U = svd.matrixU();
  Q_ASSERT(U.rows() == 3 && U.cols() == 3);
  const auto& minsv = U.col(2);
  _planeNormal = QVector3D(minsv(0), minsv(1), minsv(2));
  _planeDefined = true;
  refresh();
}

void GLView::clearPlane()
{
  _clearPlane = true;
  _planeNormal = QVector3D();
  refresh();
}

void GLView::flipPlaneNormal()
{
  if (!_planeNormal.isNull()) {
    _planeNormal = -_planeNormal;
    _planeDefined = true;
    refresh();
  }
}

} // namespace
