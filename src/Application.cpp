#include "Application.hpp"
#include "io/SettingsIO.hpp"
#include <QCoreApplication>
#include <QtQml/QQmlContext>

#include "PluginInterface.hpp"
#include <QPluginLoader>
#include <QDebug>
#include <QDir>
#include <QJsonArray>

namespace meshroom
{

Application::Application(QQmlApplicationEngine& engine)
    : QObject(nullptr)
    , _scene(new Scene(this))
{
    // expose this object to QML & load the main QML file
    engine.rootContext()->setContextProperty("_application", this);
    engine.load(QCoreApplication::applicationDirPath() + "/qml/main.qml");
}

void Application::setNodeTypes(const QStringList& nodeTypes)
{
    if(_nodeTypes == nodeTypes)
        return;
    _nodeTypes = nodeTypes;
    Q_EMIT nodeTypesChanged();
}

void Application::setNodeDescriptors(const QVariantMap& nodeDescriptors)
{
    if(_nodeDescriptors == nodeDescriptors)
        return;
    _nodeDescriptors = nodeDescriptors;
    Q_EMIT nodeDescriptorsChanged();
}

void Application::loadPlugins()
{
    PluginInterface* plugin = nullptr;
    QDir dir = QCoreApplication::applicationDirPath() + "/plugins";
    for(QString filename : dir.entryList(QDir::Files))
    {
        QPluginLoader loader(dir.absoluteFilePath(filename));

        // check metadata, before loading
        QJsonObject metadata = loader.metaData().value("MetaData").toObject();
        if(metadata.isEmpty())
            continue;
        QString name = metadata.value("name").toString();
        // load the plugin
        QObject* obj = loader.instance();
        if(!obj)
            continue;
        plugin = qobject_cast<PluginInterface*>(obj);
        if(plugin)
        {
            qInfo() << "plugin loaded:" << name.toUtf8();
            QJsonArray nodes = metadata.value("nodes").toArray();
            for(auto n : nodes)
            {
                // ...get node type
                QJsonObject nObj = n.toObject();
                QString type = nObj.value("type").toString();
                if(!type.isEmpty())
                    _nodeTypes.append(type);

                _nodeDescriptors.insert(type, nObj);
            }
        }
    }
}

} // namespace
