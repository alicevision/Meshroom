#include "Application.hpp"
#include "PluginInterface.hpp"
#include "Worker.hpp"
#include "Commands.hpp"
#include "InstantCoding.hpp"
#include <QLocale>
#include <QtQml>
#include <QCoreApplication>
#include <QPluginLoader>
#include <QSurfaceFormat>
#include <QJsonObject>
#include <QQuickStyle>
#include <QDirIterator>
#include <QDebug>
#include <signal.h>

namespace meshroom
{

Application::Application()
    : QObject(nullptr)
    , _plugins(this)
    , _pluginNodes(this)
    , _scene(this)
    , _templateScene(new Scene(this))
{
    // set global/Qt locale
    std::locale::global(std::locale::classic());
    QLocale::setDefault(QLocale::c());

    // watch unix signals
    auto handler = [](int sig)
    {
        qCritical().noquote() << "Quit.";
        QCoreApplication::quit();
    };
    signal(SIGINT, handler);
    signal(SIGTERM, handler);
    signal(SIGKILL, handler);
}

Application::Application(QQmlApplicationEngine& engine)
    : Application() // delegating constructor
{
    auto rootdir = qApp->applicationDirPath() + "/";

    // add qml modules path
    auto qmlPluginsDir = rootdir + "plugins/qml";
    engine.addImportPath(qmlPluginsDir);
    engine.addImportPath("qrc:///");

    // set qt quick style
    QQuickStyle::setStyle(rootdir + "plugins/qml/DarkStyle");

    // register types
    qRegisterMetaType<QObjectList>("QObjectList");
    qmlRegisterType<Scene>("Meshroom.Scene", 1, 0, "Scene");
    qmlRegisterType<Graph>("Meshroom.Graph", 1, 0, "Graph");
    qmlRegisterUncreatableType<Worker>("Meshroom.Worker", 1, 0, "Worker",
                                       "type registration failed (Worker)");
    qmlRegisterUncreatableType<TemplateCollection>("Meshroom.TemplateCollection", 1, 0, "TemplateCollection",
                                                   "type registration failed (TemplateCollection)");
    // set surface format
    QSurfaceFormat fmt = QSurfaceFormat::defaultFormat();
    fmt.setSamples(8);
    QSurfaceFormat::setDefaultFormat(fmt);

    // expose this object to QML
    engine.rootContext()->setContextProperty("_application", this);

    // load the main QML file
    QString qmlfile("qml/main.qml");
    auto baseUrl = QUrl::fromLocalFile(rootdir);

    QString qmlICKey("MESHROOM_DEV_QMLIC");
    auto env = QProcessEnvironment::systemEnvironment();
    bool enableIC = false;

    if(env.contains(qmlICKey))
    {
        auto qmlIC = env.value(qmlICKey);
        if( qmlIC == "1")
            enableIC = true;
        else if(QDir(qmlIC).exists())
        {
            baseUrl = QUrl::fromLocalFile(qmlIC + "/");
            enableIC = true;
        }
    }
    engine.setBaseUrl(baseUrl);

    // fill the template list
    auto templateDir = (enableIC ? baseUrl.toLocalFile() + "../" : rootdir) + "templates/";
    QDirIterator it(templateDir, QStringList{"*.meshroom"}, QDir::Files);
    while(it.hasNext())
        _templates.add(new Template(this, QUrl::fromLocalFile(it.next())));

    if(enableIC)
    {
        qDebug().noquote() << "QMLIC:" << baseUrl.toLocalFile();
        // setup qml instant coding
        auto instantCoding = new instantcoding::InstantCoding(this, engine, qmlfile);
        instantCoding->addFilesFromDirectory(templateDir);
        instantCoding->start();
    }

    engine.load(qmlfile);
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

bool Application::loadScene(const QUrl& url)
{
    return _scene.load(url);
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

void Application::openTemplate(Template* t)
{
    if(t == nullptr)
    {
        setTemplateScene(nullptr);
        return;
    }

    Scene* s = new Scene(this);
    s->setAutoRefresh(false);
    s->import(t->url());
    setTemplateScene(s);
}

void Application::createTemplateScene(const QString& graphName, const QUrl& filename)
{
    _templateScene->graph()->setProperty("name", graphName);
    _templateScene->saveAs(filename);
    setTemplateScene(nullptr);
    loadScene(filename);
}

void Application::createTemplateGraph(const QString& graphName)
{
    _templateScene->graph()->setProperty("name", graphName);
    _scene.createAndAddGraph(true, _templateScene->graph()->serializeToJSON());
    setTemplateScene(nullptr);
}

} // namespace
