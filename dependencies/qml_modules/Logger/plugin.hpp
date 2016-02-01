#pragma once

#include <QtQml>
#include <QQmlExtensionPlugin>
#include "Singleton.hpp"

namespace logger
{

void output(QtMsgType type, const QMessageLogContext& context, const QString& msg)
{
    S& singleton = S::getInstance();
    singleton.addLog(type, context, msg);
}

class LoggerQmlPlugin : public QQmlExtensionPlugin
{
    Q_OBJECT
    Q_PLUGIN_METADATA(IID "logger.qmlPlugin")

public:
    void initializeEngine(QQmlEngine* engine, const char* uri) override
    {
        qInstallMessageHandler(output);
    }
    void registerTypes(const char* uri) override
    {
        Q_ASSERT(uri == QLatin1String("Logger"));
        qmlRegisterType<LogModel>(uri, 1, 0, "LogModel");
        qmlRegisterType<Log>(uri, 1, 0, "Log");
    }
};

} // namespace
