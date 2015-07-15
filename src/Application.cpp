#include "Application.hpp"
#include "models/LogModel.hpp"
#include <iostream>

namespace mockup
{

namespace // empty namespace
{

static mockup::ApplicationModel* _logger = nullptr;
void doLog(QtMsgType type, const QMessageLogContext& context, const QString& msg)
{
    if(!_logger)
        return;
    QByteArray localMsg = msg.toLocal8Bit();
    LogModel* model = new LogModel(type, localMsg.constData(), nullptr);
    _logger->addLog(model);
}

} // empty namespace

Application::Application(QObject* parent)
    : QObject(parent)
    , _model(*this)
{
    // load user settings
    SettingsIO::loadRecentProjects(model());

    // start
    connect(&_engine, SIGNAL(objectCreated(QObject*, const QUrl&)), this,
            SLOT(onObjectCreated(QObject*, const QUrl&)));
    _engine.load(QUrl("qrc:/main.qml"));
}

Application::~Application()
{
    _logger = nullptr;
    qInstallMessageHandler(0);
}

void Application::onObjectCreated(QObject* object, const QUrl& url)
{
    // setup a custom logging system
    _logger = &model();
    qInstallMessageHandler(doLog);
}

} // namespace
