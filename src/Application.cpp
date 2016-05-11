#include "Application.hpp"
#include "io/SettingsIO.hpp"
#include <QCoreApplication>
#include <QtQml/QQmlContext>

#include "PluginInterface.hpp"
#include <QPluginLoader>
#include <QDebug>
#include <QDir>

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

void Application::loadPlugins()
{
    PluginInterface* plugin = nullptr;
    QDir dir = QCoreApplication::applicationDirPath() + "/plugins";
    for(QString filename : dir.entryList(QDir::Files))
    {
        QPluginLoader loader(dir.absoluteFilePath(filename));
        QObject* obj = loader.instance();
        if(!obj)
            continue;
        plugin = qobject_cast<PluginInterface*>(obj);
        if(plugin)
        {
            QString fullname =
                QString("%1 v%2.%3").arg(plugin->name()).arg(plugin->major()).arg(plugin->minor());
            qInfo() << "plugin loaded:" << fullname << plugin->nodeTypes();
            _nodeTypes.append(plugin->nodeTypes());
        }
    }
}

} // namespace
