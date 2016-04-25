#pragma once

#include <QVector>
#include <QTime>
#include <iostream>
#include "LogModel.hpp"

namespace logger
{

class S
{
public:
    void registerLogger(LogModel* model) { _logModels.append(model); }
    static S& getInstance()
    {
        static S instance;
        return instance;
    }
    void addLog(QtMsgType t, const QMessageLogContext& c, const QString& m)
    {
        QString msg = QTime::currentTime().toString("hh:mm:ss ").append(m);
        std::cerr << msg.toStdString() << std::endl;
#ifdef QT_MESSAGELOGCONTEXT
        if(!c.file || QString(c.file).endsWith(".qml"))
            return;
#endif
        for(auto model : _logModels)
            model->addLog(new Log(t, msg));
    }

private:
    S() = default;
    S(S const&) = delete;
    void operator=(S const&) = delete;

private:
    QVector<LogModel*> _logModels;
};

} // namespace
