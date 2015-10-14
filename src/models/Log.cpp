#include "Log.hpp"

namespace meshroom
{

Log::Log(const QtMsgType& type, const QString& message)
    : _type(type)
    , _message(message)
{
}

} // namespace
