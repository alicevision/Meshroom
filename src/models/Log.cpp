#include "Log.hpp"

namespace mockup
{

Log::Log(const QtMsgType& type, const QString& message)
    : _type(type)
    , _message(message)
{
}

} // namespace
