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
#include <cstdlib>

namespace mockup
{

// namespace // empty namespace
// {
//
// typedef std::function<void(const QUrl&)> fun_t;
// void traverseDirectory(const QUrl& url, fun_t f)
// {
//     QDir dir(url.toLocalFile());
//     if(!dir.exists())
//         return;
//     f(url);
//     QStringList list = dir.entryList(QDir::Dirs | QDir::NoSymLinks | QDir::NoDotAndDotDot);
//     for(int i = 0; i < list.size(); ++i)
//         traverseDirectory(QUrl::fromLocalFile(dir.absoluteFilePath(list[i])), f);
// }
//
// } // empty namespace

JobModel* JobsIO::create(QObject* parent)
{
    return new JobModel(parent);
}

JobModel* JobsIO::load(QObject* parent, const QUrl& url)
{
    if(!url.isValid())
    {
        qCritical("Loading job : invalid project URL (malformed or empty URL)");
        return nullptr;
    }

    QDir dir(url.toLocalFile());
    if(!dir.exists())
    {
        qCritical("Loading job : invalid project URL (not found)");
        return nullptr;
    }

    // load the job descriptor file
    QFile file(dir.filePath("job.json"));
    if(!file.open(QIODevice::ReadOnly))
    {
        qCritical("Loading job : invalid descriptor file");
        return nullptr;
    }

    // read it and close the file handler
    QByteArray data = file.readAll();
    file.close();

    // parse it as JSON
    QJsonParseError parseError;
    QJsonDocument jsondoc(QJsonDocument::fromJson(data, &parseError));
    if(parseError.error != QJsonParseError::NoError)
    {
        qCritical("Loading job : malformed descriptor file");
        return nullptr;
    }

    // create a new JobModel and set its attributes
    JobModel* jobModel = JobsIO::create(parent);
    jobModel->setUrl(url);

    // JSON: resources
    QJsonObject json = jsondoc.object();
    QJsonArray resourceArray = json["resources"].toArray();
    QObjectList resources;
    for(int i = 0; i < resourceArray.count(); ++i)
        resources.append(
            new ResourceModel(QUrl::fromLocalFile(resourceArray.at(i).toString()), jobModel));

    // JSON: steps
    QJsonObject stepsObject = json["steps"].toObject();

    // JSON: feature detection parameters
    QJsonObject featureDetectObject = stepsObject["feature_detection"].toObject();

    // JSON: structure from motion parameters
    QJsonObject sfmObject = stepsObject["sfm"].toObject();
    QJsonArray pairArray = sfmObject["initial_pair"].toArray();
    QList<QUrl> pair;
    for(int i = 0; i < pairArray.count(); ++i)
        pair.append(QUrl::fromLocalFile(pairArray.at(i).toString()));

    // JSON: meshing parameters
    QJsonObject meshingObject = stepsObject["meshing"].toObject();

    // update job parameters
    jobModel->setDate(json["date"].toString());
    jobModel->setUser(json["user"].toString());
    jobModel->setNote(json["note"].toString());
    jobModel->setResources(resources);
    jobModel->setPair(pair);
    jobModel->setMeshingScale(meshingObject["scale"].toDouble());
    jobModel->setPeakThreshold(featureDetectObject["peak_threshold"].toDouble());

    // // reset watchfolders
    // QStringList directories = _watcher.directories();
    // if(!directories.isEmpty())
    //     _watcher.removePaths(directories);
    // fun_t f = [&](const QUrl& dir)
    // {
    //     _watcher.addPath(dir.toLocalFile());
    // };
    // traverseDirectory(jobModel->buildUrl(), f);
    // traverseDirectory(jobModel->matchUrl(), f);

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
        JobModel* job = JobsIO::load(&projectModel, QUrl::fromLocalFile(dir.absoluteFilePath(jobs[i])));
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

    if(jobModel.cameras().count() < 2)
    {
        qCritical("Saving job: insufficient number of sources");
        return false;
    }

    if(jobModel.pair().count() != 2)
    {
        qCritical("Saving job: invalid initial pair");
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
    featureDetectObject["peak_threshold"] = jobModel.peakThreshold();

    // JSON: structure from motion parameters
    QJsonObject sfmObject;
    QJsonArray pairArray;
    foreach(QUrl elmt, jobModel.pair())
        pairArray.append(elmt.toLocalFile());
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

} // namespace
