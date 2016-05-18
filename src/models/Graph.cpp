#include "Graph.hpp"
#include "Application.hpp"
#include <QJsonObject>
#include <QJsonArray>
#include <QDebug>
#include <QEventLoop>

namespace meshroom
{

Graph::Graph(QObject* parent)
    : QObject(parent)
{
}

void Graph::setName(const QString& name)
{
    if(_name == name)
        return;
    _name = name;
    Q_EMIT nameChanged();
}

void Graph::addNode(const QJsonObject& descriptor)
{
    Scene* scene = qobject_cast<Scene*>(parent());
    Q_CHECK_PTR(scene);
    Application* application = qobject_cast<Application*>(scene->parent());
    Q_CHECK_PTR(application);
    // get the node type
    QString type = descriptor.value("type").toString();
    // looking for the corresponding node descriptor (registered at plugin load time)
    QVariantMap descriptors = application->nodeDescriptors();
    auto it = descriptors.find(type);
    if(it == descriptors.end())
        return;
    // merge descriptors
    QJsonObject fullDescriptor = it->toJsonObject();
    for(auto k : descriptor.keys())
        fullDescriptor.insert(k, descriptor.value(k));
    // add the node
    // TODO
    // auto node = plugin->createNode(nodeType, nodeName, _graph);
    // _graph.addNode(node);
    // reflect changes on the qml side
    Q_EMIT nodeAdded(fullDescriptor);
}

void Graph::addConnection(const QJsonObject& descriptor)
{
    // add the connection
    // TODO
    Q_EMIT connectionAdded(descriptor);
}

QJsonObject Graph::serializeToJSON() const
{
    QJsonObject obj;
    auto _CB = [&](const QJsonArray& nodes, const QJsonArray& connections)
    {
        obj.insert("nodes", nodes);
        obj.insert("connections", connections);
    };
    connect(this, &Graph::descriptionReceived, this, _CB);
    Q_EMIT descriptionRequested();
    // FIXME QEventLoop?
    obj.insert("name", _name);
    return obj;
}

void Graph::deserializeFromJSON(const QJsonObject& obj)
{
    _name = obj.value("name").toString();
    for(auto o : obj.value("nodes").toArray())
        addNode(o.toObject());
    for(auto o : obj.value("connections").toArray())
        addConnection(o.toObject());
}

} // namespace
