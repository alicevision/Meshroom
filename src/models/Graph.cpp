#include "Graph.hpp"
#include "Application.hpp"
#include "WorkerThread.hpp"
#include <QJsonObject>
#include <QJsonArray>
#include <QDebug>
#include <QDir>
#include <QMetaMethod>

using namespace dg;
namespace meshroom
{

Graph::Graph(QObject* parent)
    : QObject(parent)
    , _graph(dg::make_ptr<dg::Graph>())
{
    setCacheUrl(QUrl::fromLocalFile("/tmp"));
}

Graph::~Graph()
{
    stopWorker();
}

void Graph::setObject(QObject* obj)
{
    if(!obj)
        return;
    _qmlObject = obj;
    QObject::connect(this, SIGNAL(nodeAdded(const QJsonObject&)), _qmlObject,
                     SLOT(addNode(const QJsonObject&)));
    QObject::connect(this, SIGNAL(connectionAdded(const QJsonObject&)), _qmlObject,
                     SLOT(addConnection(const QJsonObject&)));
    QObject::connect(this, SIGNAL(nodeStatusChanged(const QString&, const QString&)), _qmlObject,
                     SLOT(updateNodeStatus(const QString&, const QString&)));
}

const bool Graph::isRunning() const
{
    if(!_worker)
        return false;
    return _worker->isRunning();
}

void Graph::setCacheUrl(const QUrl& cacheUrl)
{
    if(_cacheUrl == cacheUrl)
        return;
    // if the folder does not exist, create it
    QDir dir(cacheUrl.toLocalFile());
    if(!dir.exists())
        dir.mkpath(".");
    // save the path and set it as graph root
    _cacheUrl = cacheUrl;
    _graph->cache.setRoot(_cacheUrl.toLocalFile().toStdString());
    Q_EMIT cacheUrlChanged();
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

    // looking for node metadata (registered at plugin load time)
    PluginNode* node = application->pluginNodes()->get(type);
    if(!node)
    {
        qWarning() << "unknown node type" << type;
        return;
    }
    QJsonObject metadata = node->metadata();

    // merge metadata and current descriptor
    QVariantMap descriptorAsMap = descriptor.toVariantMap();
    for(auto k : descriptorAsMap.keys())
        metadata.insert(k, QJsonValue::fromVariant(descriptorAsMap.value(k)));

    try
    {
        // add the node
        auto dgNode = application->node(type, name);
        if(!dgNode)
        {
            qCritical() << "unable to add a" << type << "node to the current graph";
            return;
        }
        _graph->addNode(dgNode);

        // add all node attributes
        for(auto a : descriptor.value("inputs").toArray())
        {
            QJsonObject attributeObj = a.toObject();
            QString attributeKey = attributeObj.value("key").toString();
            if(attributeObj.contains("value"))
            {
                QJsonValue attribute = attributeObj.value("value");
                if(attribute.isArray())
                {
                    dg::AttributeList dgAttrList;
                    for(auto v : attribute.toArray())
                    {
                        Ptr<dg::Attribute> dgAttr = make_ptr<dg::Attribute>(
                            Attribute::Type::PATH, v.toString().toStdString());
                        dgAttrList.emplace_back(dgAttr);
                    }
                    if(!dgNode->setAttributes(attributeKey.toStdString(), dgAttrList))
                        qWarning() << "unable to set attribute list"
                                   << QString("%0::%1").arg(name).arg(attributeKey);
                    continue;
                }
                Ptr<dg::Attribute> dgAttr = make_ptr<dg::Attribute>(
                    Attribute::Type::PATH, attribute.toString().toStdString());
                if(!dgNode->setAttribute(attributeKey.toStdString(), dgAttr))
                    qWarning() << "unable to set attribute"
                               << QString("%0::%1").arg(name).arg(attributeKey);
            }
        }
    }
    catch(std::exception& e)
    {
        qCritical() << e.what();
    }

    // reflect changes on the qml side
    Q_EMIT nodeAdded(metadata);
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
    if(!_graph->connect(source->output, target->plug(plugName.toStdString())))
        qCritical() << "unable to connect nodes:" << sourceName << ">" << targetName;

    // reflect changes on the qml side
    Q_EMIT connectionAdded(connection);
}

void Graph::clear()
{
    // TODO clear _graph
    Q_EMIT cleared();
}

void Graph::startWorker(const QString& name, Graph::BuildMode mode)
{
    if(_worker && _worker->isRunning())
        return;
    delete _worker;
    _worker = new WorkerThread(this, name, mode, _graph);
    connect(_worker, &WorkerThread::nodeStatusChanged, this, &Graph::nodeStatusChanged);
    connect(_worker, &WorkerThread::finished, this, &Graph::isRunningChanged);
    _worker->start();
    Q_EMIT isRunningChanged();
}

void Graph::stopWorker()
{
    if(!isRunning())
        return;
    _worker->terminate();
    _worker->wait();
    Q_EMIT isRunningChanged();
}

QJsonObject Graph::serializeToJSON() const
{
    QJsonObject obj;
    if(!_qmlObject)
    {
        qCritical() << "can't serialize Graph: qml object not registered";
        return obj;
    }
    const QMetaObject* metaObject = _qmlObject->metaObject();
    int methodIndex = metaObject->indexOfSlot("serializeToJSON()");
    if(methodIndex == -1)
    {
        qCritical() << "can't serialize Graph: invalid object";
        return obj;
    }
    QMetaMethod method = metaObject->method(methodIndex);
    method.invoke(_qmlObject, Qt::DirectConnection, Q_RETURN_ARG(QJsonObject, obj));
    obj.insert("cacheUrl", _cacheUrl.toLocalFile());
    return obj;
}

void Graph::deserializeFromJSON(const QJsonObject& obj)
{
    setCacheUrl(QUrl::fromLocalFile(obj.value("cacheUrl").toString()));
    for(auto o : obj.value("nodes").toArray())
        addNode(o.toObject());
    for(auto o : obj.value("connections").toArray())
        addConnection(o.toObject());
}

} // namespace
