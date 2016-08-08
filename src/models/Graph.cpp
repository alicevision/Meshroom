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
                     SLOT(setNodeStatus(const QString&, const QString&)));
    QObject::connect(this, SIGNAL(cleared()), _qmlObject, SLOT(clear()));
    QObject::connect(
        this, SIGNAL(nodeAttributeChanged(const QString&, const QString&, const QVariant&)),
        _qmlObject, SLOT(setNodeAttribute(const QString&, const QString&, const QVariant&)));
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

void Graph::clear()
{
    _graph->clear();
    Q_EMIT cleared();
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

    // merge metadata and current descriptor
    QJsonObject metadata = node->metadata();
    QVariantMap descriptorAsMap = descriptor.toVariantMap();
    for(auto k : descriptorAsMap.keys())
        metadata.insert(k, QJsonValue::fromVariant(descriptorAsMap.value(k)));

    // add the node
    auto dgNode = application->node(type, name);
    if(!dgNode)
    {
        qCritical() << "unable to add a" << type << "node to the current graph";
        return;
    }
    _graph->addNode(dgNode);

    // set node attributes
    for(auto a : descriptor.value("inputs").toArray())
    {
        QString key = a.toObject().value("key").toString();
        QVariant value = a.toObject().value("value").toVariant();
        setNodeAttribute(name, key, value);
    }

    // reflect changes on the qml side
    Q_EMIT nodeAdded(metadata);
}

void Graph::addConnection(const QJsonObject& connection)
{
    // retrieve nodes
    QString sourceName = connection.value("source").toString();
    QString targetName = connection.value("target").toString();
    auto source = _graph->node(sourceName.toStdString());
    auto target = _graph->node(targetName.toStdString());
    if(!source || !target)
    {
        qCritical() << "unable to connect nodes: invalid connection";
        return;
    }

    // retrieve plug
    QString plugName = connection.value("plug").toString();
    auto plug = target->plug(plugName.toStdString());
    if(!plug)
    {
        qCritical() << "unable to connect nodes: plug" << plugName << "not found";
        return;
    }

    // connect
    if(!_graph->connect(source->output, plug))
    {
        qCritical() << "unable to connect nodes:" << sourceName << ">" << targetName;
        return;
    }

    // reflect changes on the qml side
    Q_EMIT connectionAdded(connection);
}

void Graph::setNodeAttribute(const QString& nodeName, const QString& plugName,
                             const QVariant& value)
{
    auto makeDGAttribute = [&](const QVariant& attribute) -> dg::Ptr<dg::Attribute>
    {
        switch(attribute.type())
        {
            case QVariant::Bool:
                return make_ptr<dg::Attribute>(attribute.toBool());
            case QVariant::Double:
                return make_ptr<dg::Attribute>((float)attribute.toDouble());
            case QVariant::String:
                return make_ptr<dg::Attribute>(attribute.toString().toStdString());
            default:
                break;
        }
        qCritical() << "invalid attribute value type" << value.typeName();
        return nullptr;
    };

    QVariant variant = value;
    if(!variant.isValid())
        return;
    if(variant.userType() == qMetaTypeId<QJSValue>())
        variant = qvariant_cast<QJSValue>(variant).toVariant();

    // set attribute : DG side
    auto dgNode = _graph->node(nodeName.toStdString());
    Q_CHECK_PTR(dgNode);
    if(variant.type() == QVariant::List)
    {
        dg::AttributeList attributeList;
        for(auto v : variant.toList())
            attributeList.emplace_back(makeDGAttribute(v));
        if(!dgNode->setAttributes(plugName.toStdString(), attributeList))
            qCritical() << "unable to set DG attribute list"
                        << QString("%0::%1").arg(nodeName).arg(plugName);
    }
    else
    {
        if(!dgNode->setAttribute(plugName.toStdString(), makeDGAttribute(variant)))
            qCritical() << "unable to set DG attribute"
                        << QString("%0::%1").arg(nodeName).arg(plugName);
    }

    // set attribute : QML side
    Q_EMIT nodeAttributeChanged(nodeName, plugName, variant);
}

QVariant Graph::getNodeAttribute(const QString& nodeName, const QString& plugName)
{
    auto node = _graph->node(nodeName.toStdString());
    if(!node)
        return QVariant();
    auto plug = node->plug(plugName.toStdString());
    if(!plug)
        return QVariant();
    auto attribute = _graph->cache.attribute(plug);
    return QString::fromStdString(toString(attribute));
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
    _worker->kill();
    Q_EMIT isRunningChanged();
}

QJsonObject Graph::serializeToJSON() const
{
    Q_CHECK_PTR(_qmlObject);
    QJsonObject obj;
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
