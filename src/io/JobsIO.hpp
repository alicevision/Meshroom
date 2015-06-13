#pragma once

#include <QObject>
#include <QProcess>
#include <QFileSystemWatcher>

namespace mockup
{

class JobModel; // forward declaration

class JobsIO : public QObject
{
    Q_OBJECT

public:
    JobsIO(JobModel& jobModel);

public:
    bool load();
    bool save() const;
    void start();
    void stop();
    void refresh();

private slots:
    void readProcessOutput(int exitCode, QProcess::ExitStatus exitStatus);

private:
    float computeJobCompletion();

private:
    JobModel& _job;
    QProcess _process;
    QFileSystemWatcher _watcher;
    QString _startCommand;
    QString _stopCommand;
    QString _statusCommand;
};

} // namespace
