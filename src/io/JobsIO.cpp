#include "JobsIO.hpp"
#include "models/JobModel.hpp"
#include "models/ProjectModel.hpp"
#include "models/ResourceModel.hpp"
#include <QCoreApplication>
#include <QJsonObject>
#include <QJsonArray>
#include <QJsonDocument>
#include <QFile>
#include <QDir>
#include <QDateTime>
#include <cstdlib>
#include <iostream>

namespace mockup
{

JobModel* JobsIO::load(QObject* parent, const QUrl& url)
{
    if(!url.isValid())
    {
        qCritical("Loading job : invalid project URL (malformed or empty URL)");
        return nullptr;
    }

    // create a new JobModel and set its URL and date attributes
    JobModel* jobModel = new JobModel(parent);
    jobModel->setUrl(url);
    QDateTime date = QDateTime::fromString(url.fileName(), "yyyyMMdd_HHmmss");
    jobModel->setDate(date.toString("yyyy-MM-dd HH:mm"));

    // try to load the job descriptor file
    QDir dir(url.toLocalFile());
    QFile file(dir.filePath("job.json"));
    if(file.open(QIODevice::ReadOnly))
    {
        // read all data and close the file handler
        QByteArray data = file.readAll();
        file.close();

        // parse data as JSON
        QJsonParseError parseError;
        QJsonDocument jsondoc(QJsonDocument::fromJson(data, &parseError));
        if(parseError.error != QJsonParseError::NoError)
        {
            qCritical("Loading job : malformed descriptor file");
        }
        else
        {
            // JSON: resources
            QJsonObject json = jsondoc.object();
            QJsonArray resourceArray = json["resources"].toArray();
            QObjectList resources;
            for(int i = 0; i < resourceArray.count(); ++i)
                resources.append(new ResourceModel(
                    QUrl::fromLocalFile(resourceArray.at(i).toString()), jobModel));

            // JSON: steps
            QJsonObject stepsObject = json["steps"].toObject();

            // JSON: feature detection parameters
            QJsonObject featureDetectObject = stepsObject["feature_detection"].toObject();

            // JSON: structure from motion parameters
            QJsonObject sfmObject = stepsObject["sfm"].toObject();
            QJsonArray pairArray = sfmObject["initial_pair"].toArray();

            // JSON: meshing parameters
            QJsonObject meshingObject = stepsObject["meshing"].toObject();

            // update job parameters
            // jobModel->setDate(json["date"].toString());
            jobModel->setUser(json["user"].toString());
            jobModel->setNote(json["note"].toString());
            jobModel->setResources(resources);
            if(pairArray.count() > 0)
                jobModel->setPairA(QUrl::fromLocalFile(pairArray.at(0).toString()));
            if(pairArray.count() > 1)
                jobModel->setPairB(QUrl::fromLocalFile(pairArray.at(1).toString()));
            jobModel->setMeshingScale(meshingObject["scale"].toDouble());
            jobModel->setDescriberPreset(
                JobModel::describerPresetId(featureDetectObject["describerPreset"].toString()));
        }
    }

    jobModel->autoSaveON();
    return jobModel;
}

void JobsIO::loadAllJobs(ProjectModel& projectModel)
{
    // list sub-directories to retrieve all jobs
    QDir dir(projectModel.url().toLocalFile());
    dir.cd("reconstructions");
    QStringList jobs = dir.entryList(QDir::Dirs | QDir::NoDotAndDotDot);
    QList<QObject*> validJobs;
    for(size_t i = 0; i < jobs.length(); ++i)
    {
        JobModel* job =
            JobsIO::load(&projectModel, QUrl::fromLocalFile(dir.absoluteFilePath(jobs[i])));
        if(!job)
            continue;
        validJobs.append(job);
    }
    projectModel.setJobs(validJobs);
}

bool JobsIO::save(JobModel& jobModel)
{
    if(!jobModel.url().isValid())
    {
        qCritical("Saving job: invalid project URL (malformed or empty URL)");
        return false;
    }

    // create filesystem structure
    QDir dir;
    if(!dir.mkpath(jobModel.url().toLocalFile()))
    {
        qCritical("Saving job: unable to create directory structure (job url)");
        return false;
    }

    if(!dir.mkpath(jobModel.buildUrl().toLocalFile()))
    {
        qCritical("Saving job: unable to create directory structure (build url)");
        return false;
    }

    if(!dir.mkpath(jobModel.matchUrl().toLocalFile()))
    {
        qCritical("Saving job: unable to create directory structure (match url)");
        return false;
    }

    // open file handler
    QDir rootdir(jobModel.url().toLocalFile());
    QFile file(rootdir.filePath("job.json"));
    if(!file.open(QIODevice::WriteOnly | QIODevice::Text))
    {
        qCritical("Saving job: unable to write the job descriptor file");
        return false;
    }

    // JSON: paths
    QJsonObject pathsObject;
    pathsObject["build"] = jobModel.buildUrl().toLocalFile();
    pathsObject["match"] = jobModel.matchUrl().toLocalFile();

    // JSON: resources
    QJsonArray resourceArray;
    foreach(QObject* r, jobModel.resources())
    {
        ResourceModel* resource = qobject_cast<ResourceModel*>(r);
        if(!resource)
            continue;
        resourceArray.append(resource->url().toLocalFile());
    }

    // JSON: feature detection parameters
    QJsonObject featureDetectObject;
    featureDetectObject["describerPreset"] =
        JobModel::describerPresetString(jobModel.describerPreset());

    // JSON: structure from motion parameters
    QJsonObject sfmObject;
    QJsonArray pairArray;
    pairArray.append(jobModel.pairA().toLocalFile());
    pairArray.append(jobModel.pairB().toLocalFile());
    sfmObject["initial_pair"] = pairArray;

    // JSON: meshing parameters
    QJsonObject meshingObject;
    meshingObject["scale"] = jobModel.meshingScale();

    // JSON: steps
    QJsonObject stepsObject;
    stepsObject["feature_detection"] = featureDetectObject;
    stepsObject["sfm"] = sfmObject;
    stepsObject["meshing"] = meshingObject;

    // build document
    QJsonObject json;
    json["date"] = jobModel.date();
    json["user"] = jobModel.user();
    json["note"] = jobModel.note();
    json["steps"] = stepsObject;
    json["paths"] = pathsObject;
    json["resources"] = resourceArray;

    // write document
    QJsonDocument jsondoc(json);
    file.write(jsondoc.toJson());
    file.close();
    return true;
}

void JobsIO::start(JobModel& jobModel, QProcess& process)
{
    if(jobModel.cameras().count() < 2)
    {
        qCritical("Starting job: insufficient number of sources");
        return;
    }

    if(!jobModel.pairA().isValid() || !jobModel.pairB().isValid())
    {
        qCritical("Starting job: invalid initial pair");
        return;
    }

    // set program path
    QString startCommand = std::getenv("MOCKUP_START_COMMAND");
    if(startCommand.isEmpty())
        startCommand = QCoreApplication::applicationDirPath() + "/scripts/job_start.py";
    process.setProgram(startCommand);

    // set command arguments
    QStringList arguments;
    arguments.append(jobModel.url().toLocalFile() + "/job.json");
    process.setArguments(arguments);

    // run
    process.start();
    if(!process.waitForFinished())
        qCritical("Unable to start job");
    else
        qInfo("Job started");
}

void JobsIO::stop(JobModel& jobModel, QProcess& process)
{
    // set program path
    QString stopCommand = std::getenv("MOCKUP_STOP_COMMAND");
    if(stopCommand.isEmpty())
        stopCommand = QCoreApplication::applicationDirPath() + "/scripts/job_stop.py";
    process.setProgram(stopCommand);

    // set command arguments
    QStringList arguments;
    arguments.append(jobModel.url().toLocalFile() + "/job.json");
    process.setArguments(arguments);

    // run
    process.start();
    if(!process.waitForFinished())
        qCritical("Unable to stop job");
    else
        qInfo("Job stopped");
}

void JobsIO::status(JobModel& jobModel, QProcess& process)
{
    // set program path
    QString statusCommand = std::getenv("MOCKUP_STATUS_COMMAND");
    if(statusCommand.isEmpty())
        statusCommand = QCoreApplication::applicationDirPath() + "/scripts/job_status.py";
    process.setProgram(statusCommand);

    // set command arguments
    QStringList arguments;
    arguments.append(jobModel.url().toLocalFile() + "/job.json");
    process.setArguments(arguments);

    // run
    QObject::connect(&process, SIGNAL(finished(int, QProcess::ExitStatus)), &jobModel,
                     SLOT(readProcessOutput(int, QProcess::ExitStatus)));
    process.start();
    if(!process.waitForFinished())
        qCritical("Unable to refresh job");
}

} // namespace
