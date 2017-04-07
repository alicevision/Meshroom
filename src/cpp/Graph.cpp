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
    _undoStack = scene->undoStack();

    // callbacks
    _graph.onCleared = [&, scene]()
    {
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
    return _undoStack->tryAndPush(new AddNodeCmd(this, o));
}

bool Graph::addEdge(const QJsonObject& o)
{
    return _undoStack->tryAndPush(new AddEdgeCmd(this, o));
}

bool Graph::removeNode(const QJsonObject& o)
{
    _lastCmd = new RemoveNodeCmd(this, o);
    _undoStack->tryAndPush(_lastCmd);
    _lastCmd = nullptr;
    return true;
}

bool Graph::removeEdge(const QJsonObject& o)
{
    return _undoStack->tryAndPush(new RemoveEdgeCmd(this, o));
}

bool Graph::moveNode(const QJsonObject& o)
{
    return _undoStack->tryAndPush(new MoveNodeCmd(this, o));
}

bool Graph::setAttribute(const QJsonObject& o)
{
    return _undoStack->tryAndPush(new EditAttributeCmd(this, o));
}

bool Graph::doAddNode(const QJsonObject& descriptor, QJsonObject& updatedDescriptor)
{
    // retrieve parent scene
    QObject* scene = parent();
    Q_CHECK_PTR(scene);
    // retrieve parent application
    auto application = qobject_cast<Application*>(scene->parent());
    Q_CHECK_PTR(application);
    // create a new core node
    QString nodetype = descriptor.value("type").toString();
    QString nodename = descriptor.value("name").toString();
    auto coreNode = application->createNode(nodetype, nodename);
    if(!coreNode)
    {
        qCritical() << "unable to create a new" << nodetype << "node";
        return false;
    }
    // add the node to the graph
    if(!_graph.addNode(coreNode))
        return false;
    // warn in case the name changed
    QString realname = QString::fromStdString(coreNode->name);
    updatedDescriptor = descriptor;
    updatedDescriptor.insert("name", realname);
    if(realname != nodename)
        Q_EMIT nodeNameChanged(nodename, realname);

    // get plugin node definition for this nodetype
    PluginNode* pluginNode = application->pluginNodes()->get(nodetype);
    auto typeInputs = pluginNode->metadata().value("inputs").toArray();
    auto nodeInputs = descriptor.contains("inputs") ? descriptor.value("inputs").toArray()
                                                    : QJsonArray();

    // initialize input attributes based on node definition
    for(auto a : typeInputs)
    {
        // create an attribute descriptor from type input
        QJsonObject attrDesc = a.toObject();
        // add a reference to the node
        attrDesc.insert("node", realname);
        // look for this attribute in the added node descriptor
        const auto& attr = std::find_if(nodeInputs.begin(), nodeInputs.end(),
                     [&attrDesc](const QJsonValue& obj) {
                        return obj.toObject().value("key").toString() == attrDesc.value("key").toString();
        });
        // update descriptor's 'value' with the added node attribute's 'value' if any
        if(attr != nodeInputs.end() && attr->toObject().contains("value"))
        {
            attrDesc.insert("value", attr->toObject().value("value"));
        }
        doSetAttribute(attrDesc);
    }

    // move the node
    doMoveNode(updatedDescriptor);
    return true;
}

bool Graph::doAddEdge(const QJsonObject& descriptor)
{
    if(!descriptor.contains("source") || !descriptor.contains("target") ||
       !descriptor.contains("plug"))
    {
        qCritical() << "unable to connect nodes: invalid edge description";
        return false;
    }
    // retrieve source and target nodes
    QString sourcename = descriptor.value("source").toString();
    QString targetname = descriptor.value("target").toString();
    auto coreSourceNode = _graph.node(sourcename.toStdString());
    auto coreTargetNode = _graph.node(targetname.toStdString());
    if(!coreSourceNode || !coreTargetNode)
    {
        qCritical() << "unable to connect nodes: source/target node(s) not found";
        return false;
    }
    // retrieve target plug
    QString plugname = descriptor.value("plug").toString();
    auto corePlug = coreTargetNode->plug(plugname.toStdString());
    if(!corePlug)
    {
        qCritical() << "unable to connect nodes: plug" << plugname << "not found";
        return false;
    }
    // connect the nodes
    return _graph.connect(coreSourceNode->output, corePlug);
}

bool Graph::doRemoveNode(const QJsonObject& descriptor)
{
    if(!descriptor.contains("name"))
    {
        qCritical() << "unable to remove node: invalid node name";
        return false;
    }
    // retrieve the node to delete
    QString nodename = descriptor.value("name").toString();
    auto coreNode = _graph.node(nodename.toStdString());
    if(!coreNode)
    {
        qCritical() << "unable to remove node: node" << nodename << "not found";
        return false;
    }
    // delete the node
    return _graph.removeNode(coreNode);
}

bool Graph::doRemoveEdge(const QJsonObject& descriptor)
{
    if(!descriptor.contains("source") || !descriptor.contains("target") ||
       !descriptor.contains("plug"))
    {
        qCritical() << "unable to disconnect nodes: invalid edge description";
        return false;
    }
    // retrieve source and target nodes
    QString sourcename = descriptor.value("source").toString();
    QString targetname = descriptor.value("target").toString();
    auto coreSourceNode = _graph.node(sourcename.toStdString());
    auto coreTargetNode = _graph.node(targetname.toStdString());
    if(!coreSourceNode || !coreTargetNode)
    {
        qCritical() << "unable to disconnect nodes: invalid edge";
        return false;
    }
    // retrieve target plug
    QString plugname = descriptor.value("plug").toString();
    auto corePlug = coreTargetNode->plug(plugname.toStdString());
    if(!corePlug)
    {
        qCritical() << "unable to disconnect nodes: plug" << plugname << "not found";
        return false;
    }
    // disconnect the nodes
    return _graph.disconnect(coreSourceNode->output, corePlug);
}


bool Graph::doMoveNode(const QJsonObject &descriptor)
{
    QString nodename = descriptor.value("name").toString();
    int x = descriptor.value("x").toInt();
    int y = descriptor.value("y").toInt();
    auto modelIndex = nodes()->index(nodes()->rowIndex(nodename));
    return nodes()->setData(modelIndex, QPoint(x, y),
                            nodeeditor::NodeCollection::PositionRole);
}

bool Graph::doSetAttribute(const QJsonObject &descriptor)
{
    using namespace dg;
    auto toCoreAttributeList = [&](const QVariant& attribute) -> dg::AttributeList
    {
        dg::AttributeList attributelist;
        QVariantList variantlist = (attribute.type() == QVariant::List)
                                       ? attribute.toList()
                                       : QVariantList({attribute});
        for(auto v : variantlist)
        {
            switch(v.type())
            {
                case QVariant::Bool:
                    attributelist.emplace_back(make_ptr<dg::Attribute>(v.toBool()));
                    break;
                case QVariant::Double:
                    attributelist.emplace_back(make_ptr<dg::Attribute>((float)v.toDouble()));
                    break;
                case QVariant::Int:
                    attributelist.emplace_back(make_ptr<dg::Attribute>(v.toInt()));
                    break;
                case QVariant::String:
                    attributelist.emplace_back(
                        make_ptr<dg::Attribute>(dg::FileSystemRef(v.toString().toStdString())));
                    break;
                default:
                    break;
            }
        }
        return attributelist;
    };
    // read attribute description
    QString nodename = descriptor.value("node").toString(); // added dynamically
    QString plugname = descriptor.value("key").toString();
    QVariant value = descriptor.value("value").toVariant();
    if(!value.isValid()) // may happen, in case of a connected attribute
        return false;
    // retrieve the node
    auto coreNode = _graph.node(nodename.toStdString());
    if(!coreNode)
    {
        qCritical() << "unable to edit attribute"
                    << QString("%0::%1").arg(nodename).arg(plugname) << "- node not found";
        return false;
    }
    // retrieve the plug
    auto corePlug = coreNode->plug(plugname.toStdString());
    if(!corePlug)
    {
        qCritical() << "unable to edit attribute"
                    << QString("%0::%1").arg(nodename).arg(plugname) << "- plug not found";
        return false;
    }
    // edit the attribute value
    _cache.set(corePlug, toCoreAttributeList(value));
    return true;
}

QJsonObject Graph::serializeToJSON() const
{
    QJsonObject obj;
    obj.insert("name", _name);
    obj.insert("nodes", _nodes->serializeToJSON());
    obj.insert("edges", _edges->serializeToJSON());
    return obj;
}

void Graph::deserializeFromJSON(const QJsonObject& obj)
{
    deserializeFromJSON(obj, true);
}

void Graph::deserializeFromJSON(const QJsonObject& obj, bool generateCommands)
{
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
    if(obj.contains("name"))
        _name = obj.value("name").toString();
    QJsonObject updatedDesc;
    for(auto o : obj.value("nodes").toArray())
    {
        if(generateCommands)
            addNode(o.toObject());
        else
            doAddNode(o.toObject(), updatedDesc);
    }
    for(auto o : obj.value("edges").toArray())
    {
        auto edge = o.toObject();
        changeSourceAndTargetNames(edge);
        if(generateCommands)
            addEdge(edge);
        else
            doAddEdge(edge);
    }
    disconnect(connection);
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
