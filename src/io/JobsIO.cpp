#include "JobsIO.hpp"
#include "models/JobModel.hpp"
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

namespace // empty namespace
{

typedef std::function<void(const QUrl&)> fun_t;
void traverseDirectory(const QUrl& url, fun_t f)
{
    QDir dir(url.toLocalFile());
    if(!dir.exists())
        return;
    f(url);
    QStringList list = dir.entryList(QDir::Dirs | QDir::NoSymLinks | QDir::NoDotAndDotDot);
    for(int i = 0; i < list.size(); ++i)
        traverseDirectory(QUrl::fromLocalFile(dir.absoluteFilePath(list[i])), f);
}

} // empty namespace

JobsIO::JobsIO(JobModel& jobModel)
    : QObject(&jobModel)
    , _job(jobModel)
{
    QString defaultScriptPath = QCoreApplication::applicationDirPath() + "/scripts";
    _startCommand = std::getenv("MOCKUP_START_COMMAND");
    if(_startCommand.isEmpty())
        _startCommand = defaultScriptPath + "/job_start.py";
    _stopCommand = std::getenv("MOCKUP_STOP_COMMAND");
    if(_stopCommand.isEmpty())
        _stopCommand = defaultScriptPath + "/job_stop.py";
    _statusCommand = std::getenv("MOCKUP_STATUS_COMMAND");
    if(_statusCommand.isEmpty())
        _statusCommand = defaultScriptPath + "/job_status.py";
    QObject::connect(&_watcher, SIGNAL(directoryChanged(const QString&)), &_job, SLOT(refresh()));
}

bool JobsIO::load()
{
    // set as clean
    _job.setError(JobModel::ERR_NOERROR);

    // load the job descriptor file
    if(!_job.url().isValid())
    {
        _job.setError(JobModel::ERR_INVALID_URL);
        return false;
    }

    QDir dir(_job.url().toLocalFile());
    if(!dir.exists())
    {
        _job.setError(JobModel::ERR_INVALID_URL);
        return false;
    }

    QFile file(dir.filePath("job.json"));
    if(!file.open(QIODevice::ReadOnly))
    {
        _job.setError(JobModel::ERR_INVALID_DESCRIPTOR);
        return false;
    }

    // read it and close the file handler
    QByteArray data = file.readAll();
    file.close();

    // parse it as JSON
    QJsonParseError parseError;
    QJsonDocument jsondoc(QJsonDocument::fromJson(data, &parseError));
    if(parseError.error != QJsonParseError::NoError)
    {
        _job.setError(JobModel::ERR_MALFORMED_DESCRIPTOR);
        return false;
    }

    QJsonObject json = jsondoc.object();

    // JSON: resources
    QJsonArray resourceArray = json["resources"].toArray();
    QObjectList resources;
    for(int i = 0; i < resourceArray.count(); ++i)
        resources.append(
            new ResourceModel(QUrl::fromLocalFile(resourceArray.at(i).toString()), &_job));

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
    _job.setDate(json["date"].toString());
    _job.setUser(json["user"].toString());
    _job.setNote(json["note"].toString());
    _job.setResources(resources);
    _job.setPair(pair);
    _job.setMeshingScale(meshingObject["scale"].toDouble());
    _job.setPeakThreshold(featureDetectObject["peak_threshold"].toDouble());

    // reset watchfolders
    QStringList directories = _watcher.directories();
    if(!directories.isEmpty())
        _watcher.removePaths(directories);
    fun_t f = [&](const QUrl& dir)
    {
        _watcher.addPath(dir.toLocalFile());
    };
    traverseDirectory(_job.buildUrl(), f);
    traverseDirectory(_job.matchUrl(), f);

    return true;
}

bool JobsIO::save() const
{
    // start without error
    _job.setError(JobModel::ERR_NOERROR);

    if(_job.cameras().count() < 2)
    {
        _job.setError(JobModel::ERR_SOURCE_LACK);
        return false;
    }

    if(_job.pair().count() != 2)
    {
        _job.setError(JobModel::ERR_INVALID_INITIAL_PAIR);
        return false;
    }

    // create filesystem structure
    QDir dir;
    if(!dir.mkpath(_job.url().toLocalFile()))
    {
        _job.setError(JobModel::ERR_INVALID_URL);
        return false;
    }

    if(!dir.mkpath(_job.buildUrl().toLocalFile()))
    {
        _job.setError(JobModel::ERR_INVALID_URL);
        return false;
    }

    if(!dir.mkpath(_job.matchUrl().toLocalFile()))
    {
        _job.setError(JobModel::ERR_INVALID_URL);
        return false;
    }

    // open file handler
    QDir rootdir(_job.url().toLocalFile());
    QFile file(rootdir.filePath("job.json"));
    if(!file.open(QIODevice::WriteOnly | QIODevice::Text))
    {
        _job.setError(JobModel::ERR_INVALID_DESCRIPTOR);
        return false;
    }

    // JSON: paths
    QJsonObject pathsObject;
    pathsObject["build"] = _job.buildUrl().toLocalFile();
    pathsObject["match"] = _job.matchUrl().toLocalFile();

    // JSON: resources
    QJsonArray resourceArray;
    foreach(QObject* r, _job.resources())
    {
        ResourceModel* resource = qobject_cast<ResourceModel*>(r);
        if(!resource)
            continue;
        resourceArray.append(resource->url().toLocalFile());
    }

    // JSON: feature detection parameters
    QJsonObject featureDetectObject;
    featureDetectObject["peak_threshold"] = _job.peakThreshold();

    // JSON: structure from motion parameters
    QJsonObject sfmObject;
    QJsonArray pairArray;
    foreach(QUrl elmt, _job.pair())
        pairArray.append(elmt.toLocalFile());
    sfmObject["initial_pair"] = pairArray;

    // JSON: meshing parameters
    QJsonObject meshingObject;
    meshingObject["scale"] = _job.meshingScale();

    // JSON: steps
    QJsonObject stepsObject;
    stepsObject["feature_detection"] = featureDetectObject;
    stepsObject["sfm"] = sfmObject;
    stepsObject["meshing"] = meshingObject;

    // build document
    QJsonObject json;
    json["date"] = _job.date();
    json["user"] = _job.user();
    json["note"] = _job.note();
    json["steps"] = stepsObject;
    json["paths"] = pathsObject;
    json["resources"] = resourceArray;

    // write document
    QJsonDocument jsondoc(json);
    file.write(jsondoc.toJson());
    file.close();
    return true;
}

void JobsIO::start()
{
    QStringList arguments;
    arguments.append(_job.url().toLocalFile() + "/job.json");
    _process.setArguments(arguments);
    _process.setProgram(_startCommand);
    _process.start();
}

void JobsIO::stop()
{
    QStringList arguments;
    arguments.append(_job.url().toLocalFile() + "/job.json");
    _process.setArguments(arguments);
    _process.setProgram(_stopCommand);
    _process.start();
}

void JobsIO::refresh()
{
    QObject::connect(&_process, SIGNAL(finished(int, QProcess::ExitStatus)), this,
                     SLOT(readProcessOutput(int, QProcess::ExitStatus)));
    QStringList arguments;
    arguments.append(_job.url().toLocalFile() + "/job.json");
    _process.setArguments(arguments);
    _process.setProgram(_statusCommand);
    _process.start();
}

// private
void JobsIO::readProcessOutput(int exitCode, QProcess::ExitStatus exitStatus)
{
    QObject::disconnect(&_process, SIGNAL(finished(int, QProcess::ExitStatus)), this,
                        SLOT(readProcessOutput(int, QProcess::ExitStatus)));

    // parse standard output as JSON
    QJsonParseError parseError;
    QString response(_process.readAllStandardOutput());
    QJsonDocument jsondoc(QJsonDocument::fromJson(response.toUtf8(), &parseError));
    if(parseError.error != QJsonParseError::NoError)
    {
        _job.setCompletion(computeJobCompletion());
        return;
    }

    // retrieve or compute job completion
    QJsonObject json = jsondoc.object();
    if(!json.contains("completion"))
        _job.setCompletion(computeJobCompletion());
    else
        _job.setCompletion(json["completion"].toDouble());

    // retrieve job status
    switch(json["status"].toInt())
    {
        case 0: // BLOCKED
        case 1: // READY
        case 2: // RUNNING
        case 3: // DONE
            _job.setRunning(true);
            break;
        case 4: // ERROR
        case 5: // CANCELED
        case 6: // PAUSED
            _job.setRunning(false);
            break;
    }
}

float JobsIO::computeJobCompletion()
{
    QFileInfoList fileInfoList;
    QFileInfo fileInfo;
    QDir buildDir(_job.buildUrl().toLocalFile());
    QDir matchDir(_job.matchUrl().toLocalFile());

    // final mesh (with texture)
    fileInfo.setFile(buildDir.filePath("texturing/texrecon_surface.obj"));
    if(fileInfo.exists())
        return 1.f;

    // final mesh (without texture)
    fileInfo.setFile(buildDir.filePath("mve/surface.ply"));
    if(fileInfo.exists())
        return 0.9f;

    // final (dense) pointcloud
    fileInfo.setFile(buildDir.filePath("mve/OUTPUT.ply"));
    if(fileInfo.exists())
        return 0.8f;

    // final (non-dense) pointcloud
    fileInfo.setFile(buildDir.filePath("FinalColorized.ply"));
    if(fileInfo.exists())
        return 0.7f;

    // temporary pointclouds
    size_t plyCount = 0;
    fileInfoList = buildDir.entryInfoList();
    for(int i = 0; i < fileInfoList.size(); ++i)
    {
        fileInfo = fileInfoList.at(i);
        if(fileInfo.completeSuffix() == "ply" && fileInfo.baseName().endsWith("_Resection"))
            plyCount++;
    }
    if(plyCount != 0)
        return 0.5f + 0.2f * (plyCount / (float)_job.cameras().count());

    // feature detection & matching
    matchDir.setFilter(QDir::Dirs | QDir::Files | QDir::NoSymLinks | QDir::NoDotAndDotDot);
    size_t descCount = 0;
    size_t matchCount = 0;
    fileInfoList = matchDir.entryInfoList();
    for(int i = 0; i < fileInfoList.size(); ++i)
    {
        fileInfo = fileInfoList.at(i);
        if(fileInfo.completeSuffix() == "desc")
            descCount++;
        if(fileInfo.completeSuffix() == "matches.f.txt")
            matchCount++;
    }
    if(matchCount != 0)
        return 0.2f + 0.3f * (matchCount / (float)_job.cameras().count());
    if(descCount != 0)
        return 0.2f * (descCount / (float)_job.cameras().count());

    return 0.f;
}

} // namespace
