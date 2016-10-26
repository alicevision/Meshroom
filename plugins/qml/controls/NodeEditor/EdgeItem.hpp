#pragma once

#include "Node.hpp"
#include <QQuickItem>
#include <QPainterPath>

namespace nodeeditor
{
class EdgeItem : public QQuickItem
{
    Q_OBJECT

    Q_PROPERTY(QQuickItem* sourceNode READ sourceNode WRITE setSourceNode NOTIFY sourceNodeChanged)
    Q_PROPERTY(QQuickItem* targetNode READ targetNode WRITE setTargetNode NOTIFY targetNodeChanged)

    Q_PROPERTY(QQuickItem* sourceAttr READ sourceAttr WRITE setSourceAttr NOTIFY sourceAttrChanged)
    Q_PROPERTY(QQuickItem* targetAttr READ targetAttr WRITE setTargetAttr NOTIFY targetAttrChanged)

    Q_PROPERTY(int segmentCount READ segmentCount WRITE setSegmentCount NOTIFY segmentCountChanged)
    Q_PROPERTY(QColor color READ color WRITE setColor NOTIFY colorChanged)
    Q_PROPERTY(qreal scaleFactor READ scaleFactor WRITE setScaleFactor NOTIFY scaleFactorChanged)
    Q_PROPERTY(qreal thickness READ thickness WRITE setThickness NOTIFY thicknessChanged)
    Q_PROPERTY(
        qreal hullThickness READ hullThickness WRITE setHullThickness NOTIFY hullThicknessChanged)

    Q_PROPERTY(bool containsMouse READ containsMouse NOTIFY containsMouseChanged)

    enum UpdateType
    {
        None = 0,
        Path,
        Hull,
        Vertices,
        Material,
        All,
        UpdateTypeCount
    };

public:
    EdgeItem(QQuickItem* parent = nullptr);
    virtual ~EdgeItem() {}

    int segmentCount() const { return _segmentCount; }
    void setSegmentCount(int count);

    const QColor& color() const { return _color; }
    void setColor(const QColor& color)
    {
        if(_color == color)
            return;
        _color = color;
        _updateType = Material;
        Q_EMIT colorChanged();
        update();
    }

    qreal scaleFactor() const { return _scaleFactor; }

    void setScaleFactor(qreal factor)
    {
        if(fabs(_scaleFactor - factor) < std::numeric_limits<double>::epsilon())
            return;
        _scaleFactor = factor;
        _updateType = Hull;
        Q_EMIT scaleFactorChanged();
        update();
    }

    qreal thickness() const { return _thickness; }

    void setThickness(qreal thickness)
    {
        if(fabs(_thickness - thickness) < std::numeric_limits<double>::epsilon())
            return;
        _thickness = thickness;
        _updateType = Hull;
        Q_EMIT thicknessChanged();
        update();
    }

    qreal hullThickness() const { return _hullThickness; }

    void setHullThickness(qreal thickness)
    {
        if(fabs(_hullThickness - thickness) < std::numeric_limits<double>::epsilon())
            return;
        _hullThickness = thickness;
        _updateType = Hull;
        Q_EMIT hullThicknessChanged();
        update();
    }

    QQuickItem* sourceNode() const { return _sourceNode; }
    void setSourceNode(QQuickItem* node)
    {
        updateMemberItem(_sourceNode, node);
        Q_EMIT sourceNodeChanged();
    }

    QQuickItem* targetNode() const { return _targetNode; }
    void setTargetNode(QQuickItem* node)
    {
        updateMemberItem(_targetNode, node);
        Q_EMIT targetNodeChanged();
    }

    QQuickItem* sourceAttr() const { return _sourceAttr; }
    void setSourceAttr(QQuickItem* attr)
    {
        updateMemberItem(_sourceAttr, attr);
        Q_EMIT sourceAttrChanged();
    }

    QQuickItem* targetAttr() const { return _targetNode; }
    void setTargetAttr(QQuickItem* attr)
    {
        updateMemberItem(_targetAttr, attr);
        Q_EMIT targetAttrChanged();
    }

    bool containsMouse() const { return _containsMouse; }
    void setContainsMouse(bool contains)
    {
        if(_containsMouse == contains)
            return;
        _containsMouse = contains;
        Q_EMIT containsMouseChanged();
    }

    bool contains(const QPointF& point) const override;

    QSGNode* updatePaintNode(QSGNode*, UpdatePaintNodeData*) override;

    Q_SIGNALS : void segmentCountChanged(int count);
    void colorChanged();
    void scaleFactorChanged();
    void containsMouseChanged();

    void sourceNodeChanged();
    void targetNodeChanged();
    void sourceAttrChanged();
    void targetAttrChanged();
    void thicknessChanged();
    void hullThicknessChanged();

    void pressed();
    void released();
    void doubleClicked();

protected:
    void hoverEnterEvent(QHoverEvent* event) override;
    void hoverLeaveEvent(QHoverEvent* event) override;
    void mousePressEvent(QMouseEvent* event) override;
    void mouseReleaseEvent(QMouseEvent* event) override;
    void mouseDoubleClickEvent(QMouseEvent* event) override;

    void updateBounds();
    void updateMemberItem(QQuickItem*& member, QQuickItem* newItem)
    {
        if(member == newItem)
            return;

        if(member)
            member->disconnect(this);
        member = newItem;

        if(!member)
            return;

        const auto triggerUpdate = [this]()
        {
            _updateType = Path;
            update();
        };

        connect(member, &QQuickItem::xChanged, this, triggerUpdate);
        connect(member, &QQuickItem::yChanged, this, triggerUpdate);
        connect(member, &QQuickItem::destroyed, this, [&member]()
                {
                    member = nullptr;
                });
        triggerUpdate();
    }

private:
    QQuickItem* _sourceNode = nullptr;
    QQuickItem* _targetNode = nullptr;
    QQuickItem* _sourceAttr = nullptr;
    QQuickItem* _targetAttr = nullptr;

    int _segmentCount = 32;
    QColor _color = QColor("white");
    QPainterPath _path;
    QPainterPath _hullPath;
    qreal _thickness = 2.0;
    qreal _hullThickness = 3.0;
    qreal _scaleFactor = 1.0;
    bool _containsMouse = false;

    UpdateType _updateType = EdgeItem::None;
};
}
