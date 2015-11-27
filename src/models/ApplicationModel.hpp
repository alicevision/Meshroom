#pragma once

#include <QQmlApplicationEngine>
#include "ProjectModel.hpp"
#include "ResourceModel.hpp"

namespace meshroom
{

class ApplicationModel : public QObject
{
    Q_OBJECT
    Q_PROPERTY(ProjectModel* projects READ projects NOTIFY projectsChanged)
    Q_PROPERTY(ResourceModel* featured READ featured NOTIFY featuredChanged)

public:
    ApplicationModel(QQmlApplicationEngine& engine);
    ~ApplicationModel() = default;

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
