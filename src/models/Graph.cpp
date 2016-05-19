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
    // retrieve parent scene & application
    Scene* scene = qobject_cast<Scene*>(parent());
    Q_CHECK_PTR(scene);
    Application* application = qobject_cast<Application*>(scene->parent());
    Q_CHECK_PTR(application);

    // get the node type
    QString type = descriptor.value("type").toString();

    // looking for the corresponding node descriptor (registered at plugin load time)
    NodeCollection* nodes = application->nodes();
    Node* node = nodes->get(type);
    Q_CHECK_PTR(node);
    PluginInterface* instance = node->pluginInstance();
    Q_CHECK_PTR(instance);

    // merge nodes
    QVariantMap descriptorAsMap = descriptor.toVariantMap();
    QJsonObject fullnode = node->metadata();
    for(auto k : descriptorAsMap.keys())
        fullnode.insert(k, QJsonValue::fromVariant(descriptorAsMap.value(k)));

    // add the node
    // auto dgNode = instance->createNode(type, type.toLower(), _graph);
    // _graph.addNode(dgNode);

    // reflect changes on the qml side
    Q_EMIT nodeAdded(fullnode);
}

void Graph::addConnection(const QJsonObject& node)
{
    // add the connection
    // TODO
    Q_EMIT connectionAdded(node);
}

void Graph::clear()
{
    Q_EMIT reset();
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
