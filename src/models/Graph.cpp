#include "Graph.hpp"
#include "Application.hpp"
#include "WorkerThread.hpp"
#include <QJsonObject>
#include <QJsonArray>
#include <QDebug>

using namespace dg;
namespace meshroom
{

Graph::Graph(QObject* parent)
    : QObject(parent)
{
    setCacheUrl(QUrl::fromLocalFile("/tmp"));
}

Graph::~Graph()
{
    abort();
}

const bool Graph::running() const
{
    if(!_worker)
        return false;
    return _worker->isRunning();
}

void Graph::setName(const QString& name)
{
    if(_name == name)
        return;
    _name = name;
    Q_EMIT nameChanged();
}

void Graph::setCacheUrl(const QUrl& cacheUrl)
{
    if(_cacheUrl == cacheUrl)
        return;
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
    Node* node = application->nodes()->get(type);
    Q_CHECK_PTR(node);
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
    Q_EMIT cleared();
}

void Graph::compute(const QString& name, Graph::BuildMode mode)
{
    if(_worker && _worker->isRunning())
        return;
    Q_EMIT statusCleared();
    delete _worker;
    _worker = new WorkerThread(this, name, mode, _graph);
    connect(_worker, &WorkerThread::nodeVisitStarted, this, &Graph::nodeVisitStarted);
    connect(_worker, &WorkerThread::nodeVisitCompleted, this, &Graph::nodeVisitCompleted);
    connect(_worker, &WorkerThread::nodeComputeStarted, this, &Graph::nodeComputeStarted);
    connect(_worker, &WorkerThread::nodeComputeCompleted, this, &Graph::nodeComputeCompleted);
    connect(_worker, &WorkerThread::nodeComputeFailed, this, &Graph::nodeComputeFailed);
    connect(_worker, &WorkerThread::finished, this, &Graph::runningChanged);
    _worker->start();
    Q_EMIT runningChanged();
}

void Graph::abort()
{
    if(!running())
        return;
    _worker->terminate();
    _worker->wait();
    Q_EMIT runningChanged();
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
    obj.insert("cacheUrl", _cacheUrl.toLocalFile());
    return obj;
}

void Graph::deserializeFromJSON(const QJsonObject& obj)
{
    setName(obj.value("name").toString());
    setCacheUrl(QUrl::fromLocalFile(obj.value("cacheUrl").toString()));
    for(auto o : obj.value("nodes").toArray())
        addNode(o.toObject());
    for(auto o : obj.value("connections").toArray())
        addConnection(o.toObject());
}

} // namespace
