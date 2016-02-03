#pragma once

#include <QQmlApplicationEngine>
#include "models/ProjectModel.hpp"
#include "models/ResourceModel.hpp"

namespace meshroom
{

class Application : public QObject
{
    Q_OBJECT
    Q_PROPERTY(ProjectModel* projects READ projects NOTIFY projectsChanged)
    Q_PROPERTY(ResourceModel* featured READ featured NOTIFY featuredChanged)

public:
    Application(QQmlApplicationEngine& engine);
    ~Application() = default;

public slots:
    ProjectModel* projects() const { return _projects; }
    ResourceModel* featured() const { return _featured; }

signals:
    void projectsChanged();
    void featuredChanged();

private:
    ProjectModel* _projects;
    ResourceModel* _featured;
};

} // namespaces
