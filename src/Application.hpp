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
    ~Application();

public:
    ApplicationModel& model() { return _model; }
    QQmlApplicationEngine& engine() { return _engine; }

public slots:
    void onObjectCreated(QObject* object, const QUrl& url);

private:
    QQmlApplicationEngine _engine;

private:
    ApplicationModel _model;
};

} // namespace
