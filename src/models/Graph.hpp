#pragma once

#include <QObject>
#include <dglib/dg.hpp>

namespace meshroom
{

class Application; // forward declaration

class Graph : public QObject
{
    Q_OBJECT
    Q_PROPERTY(QString name READ name WRITE setName NOTIFY nameChanged)

public:
    enum BuildMode
    {
        LOCAL = 0,
        TRACTOR = 1
    };
    Q_ENUMS(BuildMode)

public:
    Graph(QObject* parent = nullptr);

public:
    Q_SLOT const QString& name() const { return _name; }
    Q_SLOT void setName(const QString&);
    Q_SLOT void addNode(const QJsonObject&);
    Q_SLOT void addConnection(const QJsonObject&);
    Q_SLOT void compute(const QString&, BuildMode mode);
    Q_SLOT void clear();

public:
    Q_SIGNAL void nameChanged();
    Q_SIGNAL void nodeAdded(const QJsonObject& node);
    Q_SIGNAL void connectionAdded(const QJsonObject& node);
    Q_SIGNAL void descriptionRequested() const;
    Q_SIGNAL void descriptionReceived(const QJsonArray&, const QJsonArray&);
    Q_SIGNAL void cleared();

public:
    QJsonObject serializeToJSON() const;
    void deserializeFromJSON(const QJsonObject&);

private:
    QString _name = "graph1";
    dg::Ptr<dg::Graph> _graph = dg::make_ptr<dg::Graph>();
};

} // namespace
