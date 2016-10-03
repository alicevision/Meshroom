#pragma once

#include "Node.hpp"
#include <QObject>
#include <QJsonObject>

namespace nodeeditor
{

class Edge : public QObject
{
    Q_OBJECT
    Q_PROPERTY(QString source READ source WRITE setSource NOTIFY sourceChanged)
    Q_PROPERTY(QString target READ target WRITE setTarget NOTIFY targetChanged)
    Q_PROPERTY(QString plug READ plug WRITE setPlug NOTIFY plugChanged)

public:
    Edge() = default;
    Edge(const Edge& obj) = delete;
    Edge& operator=(Edge const&) = delete;

public:
    Q_SLOT const QString& source() const { return _source; }
    Q_SLOT const QString& target() const { return _target; }
    Q_SLOT const QString& plug() const { return _plug; }
    Q_SLOT int sourceID() const;
    Q_SLOT int targetID() const;
    Q_SLOT int plugID() const;
    Q_SLOT void setSource(const QString&);
    Q_SLOT void setTarget(const QString&);
    Q_SLOT void setPlug(const QString&);
    Q_SIGNAL void sourceChanged();
    Q_SIGNAL void targetChanged();
    Q_SIGNAL void plugChanged();

public:
    Q_SLOT QJsonObject serializeToJSON() const;
    Q_SLOT void deserializeFromJSON(const QJsonObject& obj);

private:
    QString _source;
    QString _target;
    QString _plug;
};

} // namespace
