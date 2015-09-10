#pragma once

#include <QObject>
#include <QProcess>

namespace mockup
{

class JobModel;     // forward declaration
class ProjectModel; // forward declaration

class JobsIO
{
public:
    static JobModel* load(QObject* parent, const QUrl& url);
    static void loadAllJobs(ProjectModel& projectModel);
    static bool save(JobModel& jobModel);
    static void start(JobModel& jobModel, QProcess& process);
    static void stop(JobModel& jobModel, QProcess& process);
    static void status(JobModel& jobModel, QProcess& process);
};

} // namespace
