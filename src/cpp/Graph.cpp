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
{
}

Graph::~Graph()
{
    stopWorker();
}

void Graph::clear()
{
    // clear
    _dgGraph.clear();

    // reflect changes on the qml side
    GET_METHOD_OR_RETURN(clear(), void());
    method.invoke(_editor, Qt::DirectConnection);

    Q_EMIT structureChanged();
}

bool Graph::addNode(const QJsonObject& descriptor)
{
    // retrieve parent scene & application
    Scene* scene = qobject_cast<Scene*>(parent());
    Q_CHECK_PTR(scene);
    Application* application = qobject_cast<Application*>(scene->parent());
    Q_CHECK_PTR(application);

    // looking for node metadata (registered at plugin load time)
    QString type = descriptor.value("type").toString();
    QString name = descriptor.value("name").toString();
    PluginNode* node = application->pluginNodes()->get(type);
    if(!node)
    {
        qWarning() << "unknown node type" << type;
        return false;
    }

    // merge metadata and current descriptor
    QJsonObject metadata = node->metadata();
    QVariantMap descriptorAsMap = descriptor.toVariantMap();
    for(auto k : descriptorAsMap.keys())
        metadata.insert(k, QJsonValue::fromVariant(descriptorAsMap.value(k)));

    // create a new node
    auto dgNode = application->createNode(type, name);
    if(!dgNode)
    {
        qCritical() << "unable to create a new" << type << "node";
        return false;
    }

    // add this new node to the graph
    if(!_dgGraph.addNode(dgNode))
    {
        qCritical() << "unable to add a" << type << "node to the current graph";
        return false;
    }

    // retrieve auto-generated name
    name = QString::fromStdString(dgNode->name);
    metadata.insert("name", name);

    // set node attributes
    for(auto a : descriptor.value("inputs").toArray())
    {
        QString key = a.toObject().value("key").toString();
        QVariant value = a.toObject().value("value").toVariant();
        setNodeAttribute(name, key, value);
    }

    // reflect changes on the qml side
    bool result = false;
    GET_METHOD_OR_RETURN(addNode(QJsonObject), false);
    method.invoke(_editor, Qt::DirectConnection, Q_RETURN_ARG(bool, result),
                  Q_ARG(QJsonObject, metadata));

    if(result)
        Q_EMIT structureChanged();

    return result;
}

bool Graph::addEdge(const QJsonObject& edge)
{
    // retrieve dg nodes
    QString sourceName = edge.value("source").toString();
    QString targetName = edge.value("target").toString();
    auto source = _dgGraph.node(sourceName.toStdString());
    auto target = _dgGraph.node(targetName.toStdString());
    if(!source || !target)
    {
        qCritical() << "unable to connect nodes: invalid edge";
        return false;
    }

    // retrieve dg plug
    QString plugName = edge.value("plug").toString();
    auto plug = target->plug(plugName.toStdString());
    if(!plug)
    {
        qCritical() << "unable to connect nodes: plug" << plugName << "not found";
        return false;
    }

    // connect dg nodes
    if(!_dgGraph.connect(source->output, plug))
    {
        qCritical() << "unable to connect nodes:" << sourceName << ">" << targetName;
        return false;
    }

    // reflect changes on the qml side
    bool result = false;
    GET_METHOD_OR_RETURN(addEdge(QJsonObject), false);
    method.invoke(_editor, Qt::DirectConnection, Q_RETURN_ARG(bool, result),
                  Q_ARG(QJsonObject, edge));

    if(result)
        Q_EMIT structureChanged();

    return result;
}

bool Graph::removeNode(const QJsonObject& descriptor)
{
    // remove the dg node
    QString nodeName = descriptor.value("name").toString();
    auto dgnode = _dgGraph.node(nodeName.toStdString());
    if(!_dgGraph.removeNode(dgnode))
        return false;

    // reflect changes on the qml side
    bool result = false;
    GET_METHOD_OR_RETURN(removeNode(QJsonObject), false);
    method.invoke(_editor, Qt::DirectConnection, Q_RETURN_ARG(bool, result),
                  Q_ARG(QJsonObject, descriptor));

    if(result)
        Q_EMIT structureChanged();

    return result;
}

bool Graph::removeEdge(const QJsonObject& descriptor)
{
    // remove the dg connection
    QString src = descriptor.value("source").toString();
    QString target = descriptor.value("target").toString();
    QString plug = descriptor.value("plug").toString();
    auto dgsrc = _dgGraph.node(src.toStdString());
    auto dgtarget = _dgGraph.node(target.toStdString());
    if(!dgsrc || !dgtarget ||
       !_dgGraph.disconnect(dgsrc->output, dgtarget->plug(plug.toStdString())))
        return false;

    // reflect changes on the qml side
    bool result = false;
    GET_METHOD_OR_RETURN(removeEdge(QJsonObject), false);
    method.invoke(_editor, Qt::DirectConnection, Q_RETURN_ARG(bool, result),
                  Q_ARG(QJsonObject, descriptor));

    if(result)
        Q_EMIT structureChanged();

    return result;
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
    auto dgNode = _dgGraph.node(nodeName.toStdString());
    if(!dgNode)
    {
        qCritical() << "unable to find node" << nodeName;
        return;
    }

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
    method.invoke(_editor, Qt::DirectConnection, Q_ARG(QString, nodeName), Q_ARG(QString, plugName),
                  Q_ARG(QVariant, variant));

    Q_EMIT structureChanged();
}

QVariant Graph::getNodeAttribute(const QString& nodeName, const QString& plugName)
{
    auto node = _dgGraph.node(nodeName.toStdString());
    if(!node)
        return QVariant();
    auto plug = node->plug(plugName.toStdString());
    if(!plug)
        return QVariant();
    auto attribute = _dgGraph.cache.attribute(plug);
    return QString::fromStdString(toString(attribute)); // FIXME
}

QUrl Graph::cacheUrl() const
{
    return QUrl::fromLocalFile(QString::fromStdString(_dgGraph.cache.root()));
}

void Graph::setCacheUrl(const QUrl& url)
{
    if(url == cacheUrl())
        return;

    // set graph root
    _dgGraph.cache.setRoot(url.toLocalFile().toStdString());

    Q_EMIT cacheUrlChanged();
}

void Graph::startWorker(BuildMode mode, const QString& name)
{
    if(_worker && _worker->isRunning())
        return;

    if(!cacheUrl().isValid())
    {
        qCritical() << "invalid cache url";
        return;
    }

    // if the cache folder does not exist, create it
    QDir dir(cacheUrl().toLocalFile());
    if(!dir.exists())
        dir.mkpath(".");

    // create worker
    delete _worker;
    _worker = new WorkerThread(this, name, mode, _dgGraph);

    // worker connections
    auto updateNodeStatuses = [&](const QString& nodeName, const QString& status)
    {
        GET_METHOD_OR_RETURN(setNodeStatus(QString, QString), void());
        method.invoke(_editor, Qt::DirectConnection, Q_ARG(QString, nodeName),
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
    Q_CHECK_PTR(_editor);
    QJsonObject obj;
    GET_METHOD_OR_RETURN(serializeToJSON(), obj);
    method.invoke(_editor, Qt::DirectConnection, Q_RETURN_ARG(QJsonObject, obj));
    obj.insert("cacheUrl", cacheUrl().toLocalFile());
    return obj;
}

void Graph::deserializeFromJSON(const QJsonObject& obj)
{
    if(obj.contains("cacheUrl"))
        setCacheUrl(QUrl::fromLocalFile(obj.value("cacheUrl").toString()));
    for(auto o : obj.value("nodes").toArray())
        addNode(o.toObject());
    for(auto o : obj.value("edges").toArray())
        addEdge(o.toObject());
}

} // namespace
