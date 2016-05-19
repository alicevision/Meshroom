#include "Application.hpp"
#include "io/SettingsIO.hpp"
#include <QCoreApplication>
#include <QtQml/QQmlContext>

#include "PluginInterface.hpp"
#include <QPluginLoader>
#include <QDebug>
#include <QDir>
#include <QJsonObject>
#include <QJsonArray>

namespace meshroom
{

Application::Application(QQmlApplicationEngine& engine)
    : QObject(nullptr)
    , _scene(this)
    , _plugins(this)
    , _nodes(this)
{
    // expose this object to QML & load the main QML file
    engine.rootContext()->setContextProperty("_application", this);
    engine.load(QCoreApplication::applicationDirPath() + "/qml/main.qml");
}

void Application::load()
{
    QDir dir = QCoreApplication::applicationDirPath() + "/plugins";
    for(QString filename : dir.entryList(QDir::Files))
    {
        // check plugin metadata, before loading
        QPluginLoader loader(dir.absoluteFilePath(filename));
        QJsonObject metadata = loader.metaData().value("MetaData").toObject();
        if(metadata.isEmpty())
            continue;
        // TODO check plugin version, node count, etc.

        // load the plugin
        PluginInterface* instance = qobject_cast<PluginInterface*>(loader.instance());
        if(!instance)
            continue;

        // register the plugin
        Plugin* plugin = new Plugin(this, metadata, instance);
        _plugins.addPlugin(plugin);

        // register all nodes
        for(auto n : metadata.value("nodes").toArray())
            _nodes.addNode(new Node(this, n.toObject(), plugin));
    }
}

} // namespace
