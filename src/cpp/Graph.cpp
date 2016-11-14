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
    QObject* scene = this->parent();
    if(!scene)
        return;

    // retrieve parent application
    _application = qobject_cast<Application*>(scene->parent());
    Q_CHECK_PTR(_application);

    // callbacks
    _graph.onCleared = [&]()
    {
        Q_CHECK_PTR(_application->undoStack());
        _application->undoStack()->clear();
        _edges->clear();
        _nodes->clear();
        Q_EMIT dataChanged();
    };
    _graph.onNodeAdded = [&](Ptr<Node> n)
    {
        QString nodetype = QString::fromStdString(n->type());
        QString nodename = QString::fromStdString(n->name);
        // retrieve node descriptor
        Q_CHECK_PTR(_application->pluginNodes());
        PluginNode* pluginnode = _application->pluginNodes()->get(nodetype);
        Q_CHECK_PTR(pluginnode);
        QJsonObject nodemetadata = pluginnode->metadata();
        // update descriptor with new name
        nodemetadata.insert("name", nodename);
        // create a new Node using this descriptor
        auto node = new nodeeditor::Node;
        node->deserializeFromJSON(nodemetadata);
        _nodes->add(node);
        Q_EMIT dataChanged();
    };
    _graph.onNodeRemoved = [&](const std::string& nodename)
    {
        _nodes->remove(QString::fromStdString(nodename));
        Q_EMIT dataChanged();
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
        Q_EMIT dataChanged();
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
        Q_EMIT dataChanged();
    };
    _graph.cache.onAttributeChanged = [&](Ptr<Plug> plug, AttributeList attr)
    {
        QString nodename = QString::fromStdString(plug->owner.name);
        QString plugname = QString::fromStdString(plug->name);
        auto attributeToQVariant = [&](Ptr<Attribute> attribute) -> QVariant
        {
            switch(attribute->_type)
            {
                case Attribute::Type::BOOL:
                    return QVariant(attribute->_bool);
                case Attribute::Type::INT:
                    return QVariant(attribute->_int);
                case Attribute::Type::FLOAT:
                    return QVariant(attribute->_float);
                case Attribute::Type::STRING:
                    return QVariant(QString::fromStdString(toString(attribute)));
            }
            return QVariant();
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
            Q_EMIT dataChanged();
            return;
        }
        // in case of an output
        att = getAttrFromCollection(node->outputs());
        if(att)
        {
            att->setValue(QJsonValue::fromVariant(attributeListToQVariant(attr)));
            Q_EMIT dataChanged();
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
    _application->tryAndPushCommand(new AddNodeCmd(this, o));
    return true;
}

bool Graph::addEdge(const QJsonObject& o)
{
    _application->tryAndPushCommand(new AddEdgeCmd(this, o));
    return true;
}

bool Graph::removeNode(const QJsonObject& o)
{
    _lastCmd = new RemoveNodeCmd(this, o);
    _application->tryAndPushCommand(_lastCmd);
    _lastCmd = nullptr;
    return true;
}

bool Graph::removeEdge(const QJsonObject& o)
{
    _application->tryAndPushCommand(new RemoveEdgeCmd(this, o));
    return true;
}

bool Graph::moveNode(const QJsonObject& o)
{
    _application->tryAndPushCommand(new MoveNodeCmd(this, o));
    return true;
}

bool Graph::setAttribute(const QJsonObject& o)
{
    _application->tryAndPushCommand(new EditAttributeCmd(this, o));
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
    _application->undoStack()->beginMacro("Import Template");
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
    _application->undoStack()->endMacro();
}

QUrl Graph::cacheUrl() const
{
    QString path = QString::fromStdString(_graph.cache.root());
    return QUrl::fromLocalFile(path);
}

void Graph::setCacheUrl(const QUrl& url)
{
    if(url == cacheUrl())
        return;
    _graph.cache.setRoot(url.toLocalFile().toStdString());
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
