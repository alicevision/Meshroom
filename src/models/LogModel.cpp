#include "LogModel.hpp"

namespace mockup
{

LogModel::LogModel(const QtMsgType& type, const QString& message, QObject* parent)
    : QObject(parent)
{
    setType(type);
    setMessage(message);
}

const int& LogModel::type() const
{
    return _type;
}

void LogModel::setType(const int& type)
{
    if(type != _type)
    {
        _type = type;
        emit typeChanged();
    }
}

const QString& LogModel::message() const
{
    return _message;
}

void LogModel::setMessage(const QString& message)
{
    if(message != _message)
    {
        _message = message;
        emit messageChanged();
    }
}

} // namespace
