#include "Job.hpp"
#include "Project.hpp"
#include <QCoreApplication>
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>
#include <QFileInfo>
#include <QDir>
#include <QDebug>
#include <cstdlib> // std::getenv
#include <cassert>

#define LOGID (QString("[job:%1]").arg(_name)).toStdString().c_str()

namespace meshroom
{

namespace // empty namespace
{

bool isRegisteredImage(const Job& job, const QUrl& url)
{
    ResourceModel* images = job.images();
    if(!images || images->rowCount() <= 0)
        return false;
    for(size_t i = 0; i < images->rowCount(); ++i)
    {
        QModelIndex id = images->index(i, 0);
        if(url == images->data(id, ResourceModel::UrlRole))
            return true;
    }
    return false;
}

} // empty namespace

Job::Job(Project* project)
    : _project(project)
    , _user(std::getenv("USER"))
    , _date(QDateTime::currentDateTime())
    , _name(_date.toString("yyyyMMdd_HHmmss"))
    , _steps(new StepModel(this))
    , _images(new ResourceModel(this))
{
    // compute job url
    if(!project)
        return;
    _url = QUrl::fromLocalFile(project->url().toLocalFile() + "/reconstructions/" +
                               _date.toString("yyyyMMdd_HHmmss"));
    // create the default graph
    createDefaultGraph();
    // activate auto-save
    autoSaveOn();
}

void Job::setName(const QString& name)
{
    if(_name == name)
        return;
    _name = name;
    emit nameChanged();
    emit dataChanged(_modelIndex, _modelIndex);
}

void Job::setCompletion(const float& completion)
{
    if(_completion == completion)
        return;
    _completion = completion;
    emit completionChanged();
    emit dataChanged(_modelIndex, _modelIndex);
}

void Job::setStatus(const StatusType& status)
{
    if(_status == status)
        return;
    _status = status;
    emit statusChanged();
    emit dataChanged(_modelIndex, _modelIndex);
}

void Job::setThumbnail(const QUrl& thumbnail)
{
    if(_thumbnail == thumbnail)
        return;
    _thumbnail = thumbnail;
    emit thumbnailChanged();
    emit dataChanged(_modelIndex, _modelIndex);
}

void Job::setModelIndex(const QModelIndex& id)
{
    _modelIndex = id;
}

bool Job::load(const QUrl& url)
{
    // return in case the job url isn't valid
    QDir dir(url.toLocalFile());
    if(!dir.exists())
    {
        qCritical() << LOGID << "malformed or empty URL '" << url.toLocalFile() << "'";
        return false;
    }
    _url = url;
    // open a file handler
    QFile jsonFile(dir.filePath("job.json"));
    if(!jsonFile.open(QIODevice::ReadOnly))
    {
        qWarning() << LOGID << "unable to read the job descriptor file" << jsonFile.fileName();
        return false;
    }
    // read it and close the file handler
    QByteArray data = jsonFile.readAll();
    jsonFile.close();
    // parse data as JSON
    QJsonParseError parseError;
    QJsonDocument jsonDocument(QJsonDocument::fromJson(data, &parseError));
    if(parseError.error != QJsonParseError::NoError)
    {
        qWarning() << LOGID << "malformed JSON file" << jsonFile.fileName();
        return false;
    }
    // read job attributes
    QJsonObject json = jsonDocument.object();
    deserializeFromJSON(json);
    return true;
}

bool Job::load(const Job& job)
{
    autoSaveOff();
    delete _images;
    delete _steps;
    _images = new ResourceModel(this, *(job.images()));
    _steps = new StepModel(this, *(job.steps()));
    _thumbnail = job.thumbnail();
    autoSaveOn();
    return true;
}

void Job::autoSaveOn()
{
    connect(_images, SIGNAL(countChanged(int)), this, SLOT(selectThumbnail()));
    connect(this, SIGNAL(nameChanged()), this, SLOT(save()));
    connect(_images, SIGNAL(countChanged(int)), this, SLOT(save()));
    for(size_t i = 0; i < _steps->rowCount(); i++)
    {
        QModelIndex id = _steps->index(i, 0);
        Step* step = _steps->data(id, StepModel::ModelDataRole).value<Step*>();
        connect(step->attributes(), SIGNAL(dataChanged(const QModelIndex&, const QModelIndex&)),
                this, SLOT(save()));
    }
}

void Job::autoSaveOff()
{
    disconnect(_images, SIGNAL(countChanged(int)), this, SLOT(selectThumbnail()));
    disconnect(this, SIGNAL(nameChanged()), this, SLOT(save()));
    disconnect(_images, SIGNAL(countChanged(int)), this, SLOT(save()));
    for(size_t i = 0; i < _steps->rowCount(); i++)
    {
        QModelIndex id = _steps->index(i, 0);
        Step* step = _steps->data(id, StepModel::ModelDataRole).value<Step*>();
        disconnect(step->attributes(), SIGNAL(dataChanged(const QModelIndex&, const QModelIndex&)),
                   this, SLOT(save()));
    }
}

bool Job::save()
{
    // return in case the job is already started
    if((int)_status >= 0)
        return false;
    // build the JSON object for this job
    QJsonObject json;
    serializeToJSON(&json);
    // create the job directory
    QDir dir;
    if(!dir.mkpath(_url.toLocalFile()))
    {
        qCritical() << LOGID << "unable to create the job directory";
        return false;
    }
    // open a file handler
    QDir jobDirectory(_url.toLocalFile());
    QFile jobFile(jobDirectory.filePath("job.json"));
    if(!jobFile.open(QIODevice::WriteOnly | QIODevice::Text))
    {
        qWarning() << LOGID << "unable to write the job descriptor file" << jobFile.fileName();
        return false;
    }
    // write & close the file handler
    QJsonDocument jsonDocument(json);
    jobFile.write(jsonDocument.toJson());
    jobFile.close();
    return true;
}

bool Job::start(bool local)
{
    // do not start a job we can't save
    if(!save())
        return false;
    // do not start an invalid job
    if(!isStartable())
        return false;
    // define the program path
    QString startCommand = std::getenv("MESHROOM_START_COMMAND");
    if(startCommand.isEmpty())
        startCommand = QCoreApplication::applicationDirPath() + "/scripts/job_start.py";
    // and add command arguments
    QStringList arguments;
    if(local)
    {
        arguments.append("--engine=local");
        arguments.append("--console");
    }
    else
        arguments.append("--engine=tractor");
    arguments.append(_url.toLocalFile() + "/job.json");
    // run the process
    QProcess process;
    process.setProgram(startCommand);
    process.setArguments(arguments);
    process.start();
    if(!process.waitForFinished())
    {
        qCritical() << LOGID << ": unable to start job";
        return false;
    }
    // and refresh the job status
    qInfo() << LOGID << "job started";
    refresh();
    return true;
}

void Job::refresh()
{
    if(!isStoredOnDisk())
    {
        setStatus(NOTSTARTED);
        return;
    }
    QFileInfo fileInfo(_url.toLocalFile() + "/job.json");
    // define program path
    QString statusCommand = std::getenv("MESHROOM_STATUS_COMMAND");
    if(statusCommand.isEmpty())
        statusCommand = QCoreApplication::applicationDirPath() + "/scripts/job_status.py";
    // and command arguments
    QStringList arguments;
    arguments.append(fileInfo.absoluteFilePath());
    // configure & run
    QProcess process;
    QObject::connect(&process, SIGNAL(finished(int, QProcess::ExitStatus)), this,
                     SLOT(readProcessOutput(int, QProcess::ExitStatus)));
    process.setProgram(statusCommand);
    process.setArguments(arguments);
    process.start();
    if(!process.waitForFinished())
    {
        qCritical() << LOGID << "unable to update job status";
        setStatus(SYSTEMERROR);
    }
}

void Job::erase()
{
    QDir dir(_url.toLocalFile());
    if(dir.exists())
        dir.removeRecursively();
}

void Job::readProcessOutput(int exitCode, QProcess::ExitStatus exitStatus)
{
    QProcess* process = qobject_cast<QProcess*>(QObject::sender());
    assert(process);

    // check exit status
    if(exitStatus != QProcess::NormalExit)
    {
        QString response(process->readAllStandardError());
        setStatus(SYSTEMERROR);
        return;
    }
    // parse standard output as JSON
    QJsonParseError parseError;
    QString response(process->readAllStandardOutput());
    QJsonDocument jsondoc(QJsonDocument::fromJson(response.toUtf8(), &parseError));
    if(parseError.error != QJsonParseError::NoError)
    {
        qCritical() << LOGID << "invalid response - parse error";
        setStatus(SYSTEMERROR);
        return;
    }
    // retrieve & set job completion & status
    QJsonObject json = jsondoc.object();
    if(!json.contains("completion") || !json.contains("status"))
    {
        qCritical() << LOGID << "invalid response - missing values";
        setStatus(SYSTEMERROR);
        return;
    }
    setCompletion(json["completion"].toDouble());
    setStatus((StatusType)json["status"].toInt());
}

void Job::selectThumbnail()
{
    QModelIndex image0ID = _images->index(0, 0);
    setThumbnail(_images->data(image0ID, ResourceModel::UrlRole).toUrl());
}

bool Job::isStoredOnDisk()
{
    QDir dir(_url.toLocalFile());
    QFile file(dir.filePath("job.json"));
    return file.exists();
}

bool Job::isStartable()
{
    if(_images->rowCount() < 2)
    {
        qCritical() << LOGID << "insufficient number of sources";
        return false;
    }
    if(!isPairValid())
    {
        qCritical() << LOGID << "invalid initial pair";
        return false;
    }
    return true;
}

bool Job::isPairA(const QUrl& url)
{
    Step* step = _steps->get("sfm");
    assert(step);
    assert(step->attributes());
    Attribute* attribute = step->attributes()->get("initial_pair");
    assert(attribute);
    QVariantList pair = attribute->value().toList();
    return (pair.count() > 0 && pair[0] == url.toLocalFile());
}

bool Job::isPairB(const QUrl& url)
{
    Step* step = _steps->get("sfm");
    assert(step);
    assert(step->attributes());
    Attribute* attribute = step->attributes()->get("initial_pair");
    assert(attribute);
    QVariantList pair = attribute->value().toList();
    return (pair.count() > 1 && pair[1] == url.toLocalFile());
}

bool Job::isPairValid()
{
    Step* step = _steps->get("sfm");
    assert(step);
    assert(step->attributes());
    Attribute* attribute = step->attributes()->get("initial_pair");
    assert(attribute);
    QVariantList pair = attribute->value().toList();
    return (pair[0].toString().isEmpty() && pair[1].toString().isEmpty()) ||
           (isRegisteredImage(*this, pair[0].toUrl()) && isRegisteredImage(*this, pair[1].toUrl()));
}

void Job::createDefaultGraph()
{
    // create feature detection step
    Step* step = new Step("feature_detection");
    Attribute* att = new Attribute();
    att->setType(2); // combo
    att->setKey("describerPreset");
    att->setName("quality");
    att->setValue("Normal");
    att->setOptions(QStringList({"Normal", "High", "Ultra"}));
    step->attributes()->addAttribute(att);
    _steps->addStep(step);
    // create meshing step
    step = new Step("meshing");
    att = new Attribute();
    att->setType(1); // slider
    att->setKey("scale");
    att->setName("meshing scale");
    att->setValue(2);
    att->setMin(1);
    att->setMax(10);
    att->setStep(1);
    step->attributes()->addAttribute(att);
    _steps->addStep(step);
    // create sfm step
    step = new Step("sfm");
    att = new Attribute();
    att->setType(3); // pair selector
    att->setKey("initial_pair");
    att->setName("initial pair");
    att->setValue(QStringList({"", ""}));
    step->attributes()->addAttribute(att);
    _steps->addStep(step);
}

void Job::serializeToJSON(QJsonObject* obj) const
{
    if(!obj)
        return;
    // build the resources array
    QJsonArray resourceArray;
    for(size_t i = 0; i < _images->rowCount(); i++)
    {
        QModelIndex id = _images->index(i, 0);
        Resource* resource = _images->data(id, ResourceModel::ModelDataRole).value<Resource*>();
        if(resource)
            resource->serializeToJSON(&resourceArray);
    }
    // build the steps object
    QJsonObject stepsObject;
    for(size_t i = 0; i < _steps->rowCount(); i++)
    {
        QModelIndex id = _steps->index(i, 0);
        Step* step = _steps->data(id, StepModel::ModelDataRole).value<Step*>();
        if(step)
            step->serializeToJSON(&stepsObject);
    }
    // then fill the main JSON object
    obj->insert("date", QJsonValue::fromVariant(_date));
    obj->insert("user", _user);
    obj->insert("name", _name);
    obj->insert("resources", resourceArray);
    obj->insert("steps", stepsObject);
}

void Job::deserializeFromJSON(const QJsonObject& obj

                              )
{
    autoSaveOff();
    // read global job settings
    if(obj.contains("user"))
        _user = obj["user"].toString();
    if(obj.contains("name"))
        _name = obj["name"].toString();
    // read job ressources
    QJsonArray resourceArray = obj["resources"].toArray();
    QObjectList resources;
    for(int i = 0; i < resourceArray.count(); ++i)
    {
        Resource* r = new Resource(QUrl::fromLocalFile(resourceArray.at(i).toString()));
        _images->addResource(r);
    }
    // read job steps (and their attributes)
    QJsonObject stepsObject = obj["steps"].toObject();
    for(size_t i = 0; i < _steps->rowCount(); i++)
    {
        QModelIndex id = _steps->index(i, 0);
        Step* step = _steps->data(id, StepModel::ModelDataRole).value<Step*>();
        if(!step)
            continue;
        step->deserializeFromJSON(stepsObject);
    }
    autoSaveOn();
}

} // namespace
