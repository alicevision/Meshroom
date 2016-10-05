#include "Application.hpp"
#include "PluginInterface.hpp"
#include <QtQml>
#include <QCoreApplication>
#include <QPluginLoader>
#include <QSurfaceFormat>
#include <QJsonObject>
#include <QJsonArray>
#include <QQuickStyle>
#include <QDebug>

namespace meshroom
{

Application::Application()
    : QObject(nullptr)
    , _scene(this)
    , _plugins(this)
    , _pluginNodes(this)
{
}

Application::Application(QQmlApplicationEngine& engine)
    : QObject(nullptr)
    , _scene(this)
    , _plugins(this)
    , _pluginNodes(this)
{
    // add qml modules path
    engine.addImportPath(qApp->applicationDirPath() + "/plugins/qml");

    // set qt quick style
    QQuickStyle::setStyle(qApp->applicationDirPath() + "/plugins/qml/DarkStyle");

    // register types
    qmlRegisterType<Scene>("Meshroom.Scene", 1, 0, "Scene");
    qmlRegisterType<Graph>("Meshroom.Graph", 1, 0, "Graph");

    // set opengl profile
    QSurfaceFormat fmt = QSurfaceFormat::defaultFormat();
    fmt.setVersion(4, 3);
    fmt.setProfile(QSurfaceFormat::CoreProfile);
    QSurfaceFormat::setDefaultFormat(fmt);

    // expose this object to QML & load the main QML file
    engine.rootContext()->setContextProperty("_application", this);
    engine.load(qApp->applicationDirPath() + "/qml/main.qml");

    // retrieve QML objects
    QList<QObject*> objects = engine.rootObjects();
    for(auto obj : objects)
    {
        QObject* editor = obj->findChild<QObject*>("nodeeditor.qmlPlugin.editor");
        if(editor != nullptr)
        {
            _scene.graph()->registerQmlObject(editor);
            break;
        }
    }
}

PluginCollection* Application::loadPlugins()
{
    QDir dir = QCoreApplication::applicationDirPath() + "/plugins/cpp";
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
        _plugins.add(plugin);

        // register all nodes
        for(auto n : metadata.value("nodes").toArray())
            _pluginNodes.add(new PluginNode(this, n.toObject(), plugin));
    }
    return &_plugins;
}

Scene* Application::loadScene(const QUrl& url)
{
    _scene.load(url);
    return &_scene;
}

dg::Ptr<dg::Node> Application::createNode(const QString& type, const QString& name)
{
    PluginNode* node = _pluginNodes.get(type);
    if(!node)
    {
        qCritical() << "unknown node type:" << type;
        return nullptr;
    }
    PluginInterface* instance = node->pluginInstance();
    Q_CHECK_PTR(instance);
    return instance->createNode(type, name);
}

} // namespace
