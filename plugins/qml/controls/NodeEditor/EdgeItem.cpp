#include "EdgeItem.hpp"

#include <QtQuick/qsgnode.h>
#include <QtQuick/qsgflatcolormaterial.h>
#include <bitset>
#include <cmath>

namespace nodeeditor
{
EdgeItem::EdgeItem(QQuickItem* parent)
    : QQuickItem(parent)
{
    setFlag(ItemHasContents, true);
    setAcceptHoverEvents(true);
    setAcceptedMouseButtons(Qt::AllButtons);
}

void EdgeItem::setSegmentCount(int count)
{
    if(_segmentCount == count)
        return;

    _segmentCount = count;
    _updateType = EdgeItem::Vertices;
    Q_EMIT segmentCountChanged(count);
    update();
}

bool EdgeItem::contains(const QPointF& point) const
{
    return _hullPath.contains(point);
}

void EdgeItem::hoverLeaveEvent(QHoverEvent*)
{
    setContainsMouse(false);
    update();
}

void EdgeItem::hoverEnterEvent(QHoverEvent*)
{
    setContainsMouse(true);
    update();
}

void EdgeItem::mousePressEvent(QMouseEvent*)
{
    Q_EMIT pressed();
}

void EdgeItem::mouseReleaseEvent(QMouseEvent*)
{
    Q_EMIT released();
}

void EdgeItem::mouseDoubleClickEvent(QMouseEvent*)
{
    Q_EMIT doubleClicked();
}

QSGNode* EdgeItem::updatePaintNode(QSGNode* oldNode, UpdatePaintNodeData*)
{
    QSGGeometryNode* node = 0;
    QSGGeometry* geometry = 0;

    if(!oldNode)
    {
        node = new QSGGeometryNode;
        geometry = new QSGGeometry(QSGGeometry::defaultAttributes_Point2D(), _segmentCount);
        geometry->setDrawingMode(GL_LINE_STRIP);
        node->setGeometry(geometry);
        node->setFlag(QSGNode::OwnsGeometry);
        QSGFlatColorMaterial* material = new QSGFlatColorMaterial;
        node->setMaterial(material);
        node->setFlag(QSGNode::OwnsMaterial);
        _updateType = EdgeItem::All; // Force full update
    }
    else
    {
        node = static_cast<QSGGeometryNode*>(oldNode);
        geometry = node->geometry();
    }
    geometry->setLineWidth(static_cast<float>(_thickness));

    std::bitset<UpdateType::UpdateTypeCount> bitset;
    bitset.set(_updateType);

    // Handle updates dependencies
    switch(_updateType)
    {
        case Path:
            bitset.set(EdgeItem::Hull);
            bitset.set(EdgeItem::Vertices);
            break;
        case All:
            bitset.set();
            break;
        default:
            break;
    }
    // Real path
    if(bitset.test(EdgeItem::Path))
    {
        if(!_sourceNode || !_targetNode || !_sourceAttr || !_targetAttr)
        {
            // Clear geometry and exit
            geometry->allocate(0);
            _path = QPainterPath();
            _hullPath = QPainterPath();
            _updateType = EdgeItem::None;
            node->markDirty(QSGNode::DirtyGeometry);
            return node;
        }
        QPointF p1 = _sourceNode->position() + _sourceNode->mapFromItem(_sourceAttr, QPointF(0, 0));
        QPointF p2 = _targetNode->position() + _targetNode->mapFromItem(_targetAttr, QPointF(0, 0));
        QPointF ctrlPtDist(fabs(p1.x() - p2.x()) * 0.7, 0);

        _path = QPainterPath(p1);
        _path.cubicTo(p1 + ctrlPtDist, p2 - ctrlPtDist, p2);
    }

    if(bitset.test(EdgeItem::Material))
    {
        auto* material = static_cast<QSGFlatColorMaterial*>(node->material());
        material->setColor(_color);
        node->markDirty(QSGNode::DirtyMaterial);
    }

    if(bitset.test(EdgeItem::Hull))
    {
        // Hull shape for mouse interaction
        qreal hullOffset = _thickness / 2.0 + (_hullThickness / _scaleFactor);
        _hullPath = QPainterPath(_path.toReversed());
        _hullPath.translate(0, -hullOffset);
        QPainterPath p = QPainterPath(_path);
        p.translate(0, hullOffset);
        _hullPath.connectPath(p);
        node->markDirty(QSGNode::DirtyGeometry);
    }

    if(bitset.test(EdgeItem::Vertices))
    {
        // Re-allocate vertices if segmentCount has changed
        if(geometry->sizeOfVertex() != _segmentCount)
        {
            geometry->allocate(_segmentCount);
        }
        QSGGeometry::Point2D* vertices = geometry->vertexDataAsPoint2D();
        for(int i = 0; i < _segmentCount; ++i)
        {
            qreal t = i / qreal(_segmentCount - 1);
            const auto point = _path.pointAtPercent(t);
            vertices[i].set(point.x(), point.y());
        }
        node->markDirty(QSGNode::DirtyGeometry);
    }

    _updateType = EdgeItem::None;
    return node;
}

void EdgeItem::updateBounds()
{
    // Not needed for mouse interaction, but
    // might be necessary for something else

    // QRectF b(_sourceNode->position(), _targetNode->position());
    // b = b.normalized();
    // setPosition(b.topLeft());
    // setSize(b.size());
}
}
