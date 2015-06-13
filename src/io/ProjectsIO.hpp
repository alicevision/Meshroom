#pragma once

#include <QObject>

namespace mockup
{

class ProjectModel; // forward declaration

class ProjectsIO : public QObject
{
    Q_OBJECT

public:
    ProjectsIO(ProjectModel& projectModel);

public:
    bool load();
    bool save() const;

private:
    ProjectModel& _project;
};

} // namespace
