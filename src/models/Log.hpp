#pragma once

#include <QObject>
#include <QString>

namespace meshroom
{

class Log : public QObject
{
public:
    Log(const QtMsgType& type, const QString& message);

public:
    const int& type() const { return _type; }
    const QString& message() const { return _message; }

private:
    int _type;
    QString _message;
};

} // namespace
