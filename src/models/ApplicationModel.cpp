#include "ApplicationModel.hpp"
#include "io/SettingsIO.hpp"
#include <QtQml/QQmlContext>
#include <iostream>

namespace mockup
{

namespace // empty namespace
{

static mockup::ApplicationModel* _logger = nullptr;
void doLog(QtMsgType type, const QMessageLogContext& context, const QString& msg)
{
    if(!_logger || !_logger->logs())
        return;
    QByteArray localMsg = msg.toLocal8Bit();
    if(QString(context.file).contains(".qml"))
    {
        std::cerr << localMsg.constData() << std::endl;
        return;
    }
    Log* log = new Log(type, localMsg.constData());
    _logger->logs()->addLog(log);
}

} // empty namespace

ApplicationModel::ApplicationModel(QQmlApplicationEngine& engine)
    : QObject(nullptr)
    , _logs(new LogModel(this))
    , _projects(new ProjectModel(this))
    , _featured(new ResourceModel(this))
{
    // initialize recent and featured project lists
    SettingsIO::loadRecentProjects(_projects);
    SettingsIO::loadFeaturedProjects(_featured);
    // expose this object to QML
    if(engine.rootContext())
        engine.rootContext()->setContextProperty("_applicationModel", this);
    // load the main QML file
    connect(&engine, SIGNAL(objectCreated(QObject*, const QUrl&)), this,
            SLOT(onEngineLoaded(QObject*, const QUrl&)));
    engine.load(QUrl("src/qml/main.qml"));
}

ApplicationModel::~ApplicationModel()
{
    _logger = this;
    qInstallMessageHandler(0);
}

void ApplicationModel::onEngineLoaded(QObject* object, const QUrl& url)
{
    // setup a custom logging system
    _logger = this;
    qInstallMessageHandler(doLog);
}

} // namespace
