#include "Graph.hpp"
#include "Application.hpp"
#include <QJsonObject>
#include <QJsonArray>
#include <QDebug>
#include <QEventLoop>

using namespace dg;
namespace meshroom
{

Graph::Graph(QObject* parent)
    : QObject(parent)
{
    _graph->cache.setRoot("/tmp/");
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
    QString name = descriptor.value("name").toString();

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
    _graph->addNode(instance->createNode(type, name));

    // reflect changes on the qml side
    Q_EMIT nodeAdded(fullnode);
}

void Graph::addConnection(const QJsonObject& connection)
{
    // retrieve nodes
    QString sourceName = connection.value("source").toString();
    QString targetName = connection.value("target").toString();
    QString plugName = connection.value("plug").toString();

    // add the connection
    auto source = _graph->node(sourceName.toStdString());
    auto target = _graph->node(targetName.toStdString());
    if(!source || !target)
        return;
    _graph->connect(source->output, target->plug(plugName.toStdString()));

    // reflect changes on the qml side
    Q_EMIT connectionAdded(connection);
}

void Graph::clear()
{
    Q_EMIT reset();
}

void Graph::compute(const QString& name)
{
    qWarning() << "computing " << name;
    LocalRunner runner;
    try {
        runner(_graph, name.toStdString());
    } catch (std::exception& e) {
        qCritical() << e.what();
    }
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
