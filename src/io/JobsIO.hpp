#pragma once

#include <QObject>

namespace mockup
{

class JobModel;     // forward declaration
class ProjectModel; // forward declaration

class JobsIO
{
public:
    static JobModel* create(QObject* parent);
    static JobModel* load(QObject* parent, const QUrl& url);
    static void loadAllJobs(ProjectModel& projectModel);
    static bool save(JobModel& projectModel);
};

} // namespace
