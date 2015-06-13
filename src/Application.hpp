#pragma once

#include "models/ApplicationModel.hpp"
#include "io/SettingsIO.hpp"
#include <QObject>
#include <QtQml/QQmlApplicationEngine>

namespace mockup
{

class Application : public QObject
{
    Q_OBJECT

public:
    Application(QObject* parent = nullptr);
    ~Application() = default;

public:
    ApplicationModel& model() { return _model; }
    QQmlApplicationEngine& engine() { return _engine; }
    SettingsIO& settings() { return _settings; }

private:
    QQmlApplicationEngine _engine;

private:
    ApplicationModel _model;
    SettingsIO _settings;
};

} // namespace
