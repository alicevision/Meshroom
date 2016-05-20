#pragma once

#include <QObject>

namespace nodeeditor
{

class Connection : public QObject
{
    Q_OBJECT
    Q_PROPERTY(QString source READ source WRITE setSource NOTIFY sourceChanged)
    Q_PROPERTY(QString target READ target WRITE setTarget NOTIFY targetChanged)
    Q_PROPERTY(QString plug READ plug WRITE setSlot NOTIFY plugChanged)

public:
    Connection() = default;
    Connection(const Connection& obj) = delete;
    Connection& operator=(Connection const&) = delete;

public:
    Q_SLOT const QString& source() const { return _source; }
    Q_SLOT const QString& target() const { return _target; }
    Q_SLOT const QString& plug() const { return _plug; }
    Q_SLOT void setSource(const QString&);
    Q_SLOT void setTarget(const QString&);
    Q_SLOT void setSlot(const QString&);
    Q_SIGNAL void sourceChanged();
    Q_SIGNAL void targetChanged();
    Q_SIGNAL void plugChanged();

public:
    QJsonObject serializeToJSON() const;
    void deserializeFromJSON(const QJsonObject& obj);

private:
    QString _source;
    QString _target;
    QString _plug;
};

} // namespace
