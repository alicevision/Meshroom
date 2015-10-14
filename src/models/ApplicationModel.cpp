#include "ApplicationModel.hpp"
#include "io/SettingsIO.hpp"
#include <QCoreApplication>
#include <QtQml/QQmlContext>
#include <iostream>

namespace meshroom
{

namespace // empty namespace
{

static ApplicationModel* _logger = nullptr;

void doLog(QtMsgType type, const QMessageLogContext& context, const QString& msg)
{
    if(!_logger || !_logger->logs())
        return;
    QByteArray localMsg = msg.toLocal8Bit();
    if(QString(context.file).contains(".qml"))
    {
#ifndef NDEBUG
        std::cerr << localMsg.constData() << std::endl;
#endif
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
    // setup a custom logging system
    _logger = this;
    qInstallMessageHandler(doLog);

    // initialize recent and featured project lists
    SettingsIO::loadRecentProjects(_projects);
    SettingsIO::loadFeaturedProjects(_featured);

    // expose this object to QML & load the main QML file
    if(engine.rootContext())
        engine.rootContext()->setContextProperty("_applicationModel", this);
#ifndef NDEBUG
    engine.load("src/qml/main_debug.qml");
#else
    engine.load(QCoreApplication::applicationDirPath() + "/qml/main.qml");
#endif
}

ApplicationModel::~ApplicationModel()
{
    _logger = this;
    qInstallMessageHandler(0);
}

} // namespace
