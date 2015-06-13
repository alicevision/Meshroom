#include "Application.hpp"

namespace mockup
{

Application::Application(QObject* parent)
    : QObject(parent)
    , _model(*this)
    , _settings(*this)
{
    _settings.load();
    _engine.load(QUrl("qrc:/main.qml"));
}

} // namespace
