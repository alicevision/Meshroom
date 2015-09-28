#pragma once

#include <QQmlApplicationEngine>
#include "ProjectModel.hpp"
#include "LogModel.hpp"
#include "ResourceModel.hpp"

namespace mockup
{

class ApplicationModel : public QObject
{
    Q_OBJECT
    Q_PROPERTY(ProjectModel* projects READ projects NOTIFY projectsChanged)
    Q_PROPERTY(LogModel* logs READ logs NOTIFY logsChanged)
    Q_PROPERTY(ResourceModel* featured READ featured NOTIFY featuredChanged)

public:
    ApplicationModel(QQmlApplicationEngine& engine);
    ~ApplicationModel();

public slots:
    ProjectModel* projects() const { return _projects; }
    LogModel* logs() const { return _logs; }
    ResourceModel* featured() const { return _featured; }

public slots:
    void onEngineLoaded(QObject* object, const QUrl& url);

signals:
    void projectsChanged();
    void logsChanged();
    void featuredChanged();

private:
    ProjectModel* _projects;
    LogModel* _logs;
    ResourceModel* _featured;
};

} // namespaces
