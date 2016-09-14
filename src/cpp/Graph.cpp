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

void Graph::clear()
{
    // clear
    _graph->clear();

    // reflect changes on the qml side
    GET_METHOD_OR_RETURN(clear(), void());
    method.invoke(_qmlEditor, Qt::DirectConnection);
}

void Graph::addNode(const QJsonObject& descriptor)
{
    // retrieve parent scene & application
    Scene* scene = qobject_cast<Scene*>(parent());
    Q_CHECK_PTR(scene);
    Application* application = qobject_cast<Application*>(scene->parent());
    Q_CHECK_PTR(application);

    // looking for node metadata (registered at plugin load time)
    QString type = descriptor.value("type").toString();
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

    // compute node name
    QString name = descriptor.value("name").toString();
    if(name.isEmpty())
    {
        metadata.insert("name", type.toLower());
        name = descriptor.value("name").toString();
    }

    // create a new node
    auto dgNode = application->createNode(type, name);
    if(!dgNode)
    {
        qCritical() << "unable to create a new" << type << "node";
        return;
    }

    // add this new node to the graph
    if(!_graph->addNode(dgNode))
    {
        qCritical() << "unable to add a" << type << "node to the current graph";
        return;
    }

    // set node attributes
    for(auto a : descriptor.value("inputs").toArray())
    {
        QString key = a.toObject().value("key").toString();
        QVariant value = a.toObject().value("value").toVariant();
        setNodeAttribute(name, key, value);
    }

    // reflect changes on the qml side
    GET_METHOD_OR_RETURN(addNode(QJsonObject), void());
    method.invoke(_qmlEditor, Qt::DirectConnection, Q_ARG(QJsonObject, metadata));
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
    GET_METHOD_OR_RETURN(addConnection(QJsonObject), void());
    method.invoke(_qmlEditor, Qt::DirectConnection, Q_ARG(QJsonObject, connection));
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

    // reflect changes on the qml side
    GET_METHOD_OR_RETURN(setNodeAttribute(QString, QString, QVariant), void());
    method.invoke(_qmlEditor, Qt::DirectConnection, Q_ARG(QString, nodeName),
                  Q_ARG(QString, plugName), Q_ARG(QVariant, variant));
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
    return QString::fromStdString(toString(attribute)); // FIXME
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

void Graph::startWorker(BuildMode mode, const QString& name)
{
    if(_worker && _worker->isRunning())
        return;

    // create worker
    delete _worker;
    _worker = new WorkerThread(this, name, mode, _graph);

    // worker connections
    auto updateNodeStatuses = [&](const QString& nodeName, const QString& status)
    {
        GET_METHOD_OR_RETURN(setNodeStatus(QString, QString), void());
        method.invoke(_qmlEditor, Qt::DirectConnection, Q_ARG(QString, nodeName),
                      Q_ARG(QString, status));
    };
    connect(_worker, &WorkerThread::nodeStatusChanged, this, updateNodeStatuses);
    connect(_worker, &WorkerThread::finished, this, &Graph::isRunningChanged);

    // start worker
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

const bool Graph::isRunning() const
{
    if(!_worker)
        return false;
    return _worker->isRunning();
}

QJsonObject Graph::serializeToJSON() const
{
    Q_CHECK_PTR(_qmlEditor);

    QJsonObject obj;
    GET_METHOD_OR_RETURN(serializeToJSON(), obj);
    method.invoke(_qmlEditor, Qt::DirectConnection, Q_RETURN_ARG(QJsonObject, obj));
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
