#include "Graph.hpp"
#include "Application.hpp"
#include "WorkerThread.hpp"
#include "Commands.hpp"
#include <nodeEditor/Node.hpp>
#include <nodeEditor/Edge.hpp>
#include <QJsonObject>
#include <QDebug>
#include <QPoint>

using namespace dg;
namespace meshroom
{

Graph::Graph(QObject* parent)
    : nodeeditor::AbstractGraph(parent)
{
    // retrieve parent scene
    Scene* scene = qobject_cast<Scene*>(parent);
    if(!scene)
        return;

    // retrieve parent application
    auto application = qobject_cast<Application*>(scene->parent());
    Q_CHECK_PTR(application);

    // callbacks
    _graph.onCleared = [&, scene]()
    {
        Q_CHECK_PTR(scene->undoStack());
        scene->undoStack()->clear();
        _edges->clear();
        _nodes->clear();
    };
    _graph.onNodeAdded = [&, application](Ptr<Node> n)
    {
        QString nodetype = QString::fromStdString(n->type());
        QString nodename = QString::fromStdString(n->name);
        // retrieve node descriptor
        Q_CHECK_PTR(application->pluginNodes());
        PluginNode* pluginnode = application->pluginNodes()->get(nodetype);
        Q_CHECK_PTR(pluginnode);
        QJsonObject nodemetadata = pluginnode->metadata();
        // update descriptor with new name
        nodemetadata.insert("name", nodename);
        // create a new Node using this descriptor
        auto node = new nodeeditor::Node;
        node->deserializeFromJSON(nodemetadata);
        _nodes->add(node);
    };
    _graph.onNodeRemoved = [&](const std::string& nodename)
    {
        _nodes->remove(QString::fromStdString(nodename));
    };
    _graph.onEdgeAdded = [&](Ptr<Plug> src, Ptr<Plug> target)
    {
        // create edge descriptor
        QJsonObject o;
        o.insert("source", QString::fromStdString(src->owner.name));
        o.insert("target", QString::fromStdString(target->owner.name));
        o.insert("plug", QString::fromStdString(target->name));
        // create a new Edge using this descriptor
        auto edge = new nodeeditor::Edge(*_nodes);
        edge->deserializeFromJSON(o);
        _edges->add(edge);
    };
    _graph.onEdgeRemoved = [&](Ptr<Plug> src, Ptr<Plug> target)
    {
        // create edge descriptor
        QJsonObject o;
        o.insert("source", QString::fromStdString(src->owner.name));
        o.insert("target", QString::fromStdString(target->owner.name));
        o.insert("plug", QString::fromStdString(target->name));
        // remove edge
        _edges->remove(o);
        // add a child command
        new RemoveEdgeCmd(this, o, _lastCmd);
    };
    _cache.onAttributeChanged = [&](Ptr<Plug> plug, AttributeList attr)
    {
        QString nodename = QString::fromStdString(plug->owner.name);
        QString plugname = QString::fromStdString(plug->name);
        auto attributeToQVariant = [&](Ptr<Attribute> attribute) -> QVariant
        {
            if(attribute->variant.is<bool>())
                return QVariant(attribute->get<bool>());
            if(attribute->variant.is<int>())
                return QVariant(attribute->get<int>());
            if(attribute->variant.is<float>())
                return QVariant(attribute->get<float>());
            return QVariant(QString::fromStdString(attribute->toString()));
        };
        auto attributeListToQVariant = [&](AttributeList attributes) -> QVariant
        {
            if(attributes.size() == 1)
                return attributeToQVariant(attributes[0]);
            QVariantList list;
            for(auto& a : attributes)
                list.append(attributeToQVariant(a));
            return list;
        };
        auto getAttrFromCollection = [&](
            nodeeditor::AttributeCollection* collection) -> nodeeditor::Attribute*
        {
            int id = collection->rowIndex(plugname);
            if(id < 0)
                return nullptr;
            auto modelIndex = collection->index(id);
            return collection->data(modelIndex, nodeeditor::AttributeCollection::ModelDataRole)
                .value<nodeeditor::Attribute*>();
        };
        // retrieve ui node
        auto modelIndex = _nodes->index(_nodes->rowIndex(nodename));
        auto node = _nodes->data(modelIndex, nodeeditor::NodeCollection::ModelDataRole)
                        .value<nodeeditor::Node*>();
        if(!node)
        {
            qCritical() << "unable to update attribute value, node" << nodename << "not found";
            return;
        }
        // retrieve and set ui attribute
        // in case of an input
        nodeeditor::Attribute* att = getAttrFromCollection(node->inputs());
        if(att)
        {
            att->setValue(QJsonValue::fromVariant(attributeListToQVariant(attr)));
            return;
        }
        // in case of an output
        att = getAttrFromCollection(node->outputs());
        if(att)
        {
            att->setValue(QJsonValue::fromVariant(attributeListToQVariant(attr)));
            return;
        }
        qCritical() << "unable to update attribute value, attribute" << plugname << "not found";
    };
}

Graph::~Graph()
{
    stopWorkerThread();
}

void Graph::clear()
{
    _graph.clear();
}

bool Graph::addNode(const QJsonObject& o)
{
    Scene* scene = qobject_cast<Scene*>(parent());
    scene->undoStack()->tryAndPush(new AddNodeCmd(this, o));
    return true;
}

bool Graph::addEdge(const QJsonObject& o)
{
    Scene* scene = qobject_cast<Scene*>(parent());
    scene->undoStack()->tryAndPush(new AddEdgeCmd(this, o));
    return true;
}

bool Graph::removeNode(const QJsonObject& o)
{
    _lastCmd = new RemoveNodeCmd(this, o);
    Scene* scene = qobject_cast<Scene*>(parent());
    scene->undoStack()->tryAndPush(_lastCmd);
    _lastCmd = nullptr;
    return true;
}

bool Graph::removeEdge(const QJsonObject& o)
{
    Scene* scene = qobject_cast<Scene*>(parent());
    scene->undoStack()->tryAndPush(new RemoveEdgeCmd(this, o));
    return true;
}

bool Graph::moveNode(const QJsonObject& o)
{
    Scene* scene = qobject_cast<Scene*>(parent());
    scene->undoStack()->tryAndPush(new MoveNodeCmd(this, o));
    return true;
}

bool Graph::setAttribute(const QJsonObject& o)
{
    Scene* scene = qobject_cast<Scene*>(parent());
    scene->undoStack()->tryAndPush(new EditAttributeCmd(this, o));
    return true;
}

QJsonObject Graph::serializeToJSON() const
{
    QJsonObject obj;
    obj.insert("cacheUrl", cacheUrl().toLocalFile());
    obj.insert("nodes", _nodes->serializeToJSON());
    obj.insert("edges", _edges->serializeToJSON());
    return obj;
}

void Graph::deserializeFromJSON(const QJsonObject& obj)
{
    Scene* scene = qobject_cast<Scene*>(parent());
    scene->undoStack()->beginMacro("Import Template");
    // callback used when a node changes name
    QMap<QString, QString> renamedNodes;
    auto onNodeNameChanged = [&](const QString& oldname, const QString& newname)
    {
        renamedNodes.insert(oldname, newname);
    };
    auto connection =
        connect(this, &Graph::nodeNameChanged, this, onNodeNameChanged, Qt::DirectConnection);
    // lambda used to update edge's data with new source and target names
    auto changeSourceAndTargetNames = [&](QJsonObject& edge)
    {
        // replace source name
        auto it = renamedNodes.find(edge.value("source").toString());
        if(it != renamedNodes.end())
            edge.insert("source", it.value());
        // replace target name
        it = renamedNodes.find(edge.value("target").toString());
        if(it != renamedNodes.end())
            edge.insert("target", it.value());
    };
    // serialize
    if(obj.contains("cacheUrl"))
        setCacheUrl(QUrl::fromLocalFile(obj.value("cacheUrl").toString()));
    for(auto o : obj.value("nodes").toArray())
        addNode(o.toObject());
    for(auto o : obj.value("edges").toArray())
    {
        auto edge = o.toObject();
        changeSourceAndTargetNames(edge);
        addEdge(edge);
    }
    disconnect(connection);
    scene->undoStack()->endMacro();
}

QUrl Graph::cacheUrl() const
{
    QString path = QString::fromStdString(_environment.get(Environment::Key::CACHE_DIRECTORY));
    return QUrl::fromLocalFile(path);
}

void Graph::setCacheUrl(const QUrl& url)
{
    if(url == cacheUrl())
        return;
    _environment.push(Environment::Key::CACHE_DIRECTORY, url.toLocalFile().toStdString());
    Q_EMIT cacheUrlChanged();
}

void Graph::startWorkerThread(Worker::Mode mode, const QString& node)
{
    if(isWorkerThreadRunning())
        return;
    // create a worker
    Worker* worker = new Worker(this);
    worker->setMode(mode);
    worker->setNode(node);
    // lamda, used to convert runner::status to node::status
    auto toNodeStatus = [&](Runner::NodeStatus status) -> nodeeditor::Node::Status
    {
        switch(status)
        {
            case Runner::NodeStatus::READY:
                return nodeeditor::Node::READY;
            case Runner::NodeStatus::WAITING:
                return nodeeditor::Node::WAITING;
            case Runner::NodeStatus::RUNNING:
                return nodeeditor::Node::RUNNING;
            case Runner::NodeStatus::ERROR:
                return nodeeditor::Node::ERROR;
            case Runner::NodeStatus::DONE:
                return nodeeditor::Node::DONE;
        }
    };
    // callback, called when a node status has changed
    auto onStatusChanged = [&](const Node& node, Runner::NodeStatus status, const std::string& msg)
    {
        QString nodename = QString::fromStdString(node.name);
        auto modelIndex = _nodes->index(_nodes->rowIndex(nodename));
        _nodes->setData(modelIndex, toNodeStatus(status), nodeeditor::NodeCollection::StatusRole);
        if(msg.empty())
            return;
        QDebug output = (status == Runner::NodeStatus::ERROR) ? qCritical() : qInfo();
        output << QString::fromStdString(msg);
    };
    worker->onStatusChanged = onStatusChanged;
    // create thread
    delete _thread;
    _thread = new WorkerThread(this, worker); // will take worker ownership
    connect(_thread, &WorkerThread::finished, this, &Graph::isRunningChanged);
    // start thread
    _thread->start();
    Q_EMIT isRunningChanged();
}

void Graph::stopWorkerThread()
{
    if(!isWorkerThreadRunning())
        return;
    _thread->kill();
    _thread->wait();
    Q_EMIT isRunningChanged();
}

bool Graph::isWorkerThreadRunning() const
{
    if(!_thread)
        return false;
    return _thread->isRunning();
}

} // namespace
