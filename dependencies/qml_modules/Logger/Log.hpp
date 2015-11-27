#pragma once

#include <QObject>
#include <QString>

namespace logger
{

class Log : public QObject
{
    Q_OBJECT
    Q_PROPERTY(MsgType type READ type)
    Q_PROPERTY(QString message READ message)

public:
    enum MsgType
    {
        INFO = QtInfoMsg,
        DEBUG = QtDebugMsg,
        WARNING = QtWarningMsg,
        CRITICAL = QtCriticalMsg,
        FATAL = QtFatalMsg
    };
    Q_ENUMS(MsgType)

public:
    Log() = default;
    Log(const QtMsgType& type, const QString& message)
        : _type((MsgType)type)
        , _message(message)
    {
    }

public:
    const MsgType& type() const { return _type; }
    const QString& message() const { return _message; }

private:
    MsgType _type;
    QString _message;
};

} // namespace
