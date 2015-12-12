#include "Job.hpp"
#include "JobModel.hpp"
#include <QCoreApplication>
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>
#include <QFileInfo>
#include <QDir>
#include <QDebug>
#include <cstdlib> // std::getenv
#include <cassert>
#include <iostream>

namespace meshroom
{

namespace // empty namespace
{

Attribute* getAttribute(const Job& job, const QString& stepName, const QString& attrKey,
                        QModelIndex& outIndex, Step** outStep)
{
    if(!job.steps())
        return nullptr;
    for(size_t i = 0; i < job.steps()->rowCount(); i++)
    {
        QModelIndex id = job.steps()->index(i, 0);
        Step* step = job.steps()->data(id, StepModel::ModelDataRole).value<Step*>();
        if(step && step->name() != stepName)
            continue;
        for(size_t i = 0; i < step->attributes()->rowCount(); i++)
        {
            QModelIndex id = step->attributes()->index(i, 0);
            Attribute* att =
                step->attributes()->data(id, AttributeModel::ModelDataRole).value<Attribute*>();
            if(att && att->key() != attrKey)
                continue;
            outIndex = id;
            *outStep = step;
            return att;
        }
    }
    return nullptr;
}

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

Job::Job(const QUrl& url)
    : _url(url)
    , _name(_url.fileName())
    , _steps(new StepModel(this))
    , _images(new ResourceModel(this))
    , _user(std::getenv("USER"))
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
    att = new Attribute();
    att->setType(2); // combo
    att->setKey("method");
    att->setName("method");
    att->setValue("SIFT");
    att->setOptions(QStringList({"SIFT", "CCTAG3", "SIFT_CCTAG3"}));
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
    att = new Attribute();
    att->setType(2); // combo
    att->setKey("enabled");
    att->setName("Meshing");
    att->setValue("0");
    att->setOptions(QStringList({"1", "0"}));
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

    // create sfm step
    step = new Step("undistort");
    att = new Attribute();
    att->setType(2); // combo
    att->setKey("enabled");
    att->setName("Undistort");
    att->setValue("0");
    att->setOptions(QStringList({"1", "0"}));
    step->attributes()->addAttribute(att);
    _steps->addStep(step);

    // load job settings
    load();
    // signal/slot connection: initial_pair automatic selection
    QObject::connect(_images, SIGNAL(countChanged(int)), this, SLOT(selectPair()));
    // signal/lot connection: thumbnail selection
    QObject::connect(_images, SIGNAL(countChanged(int)), this, SLOT(selectThumbnail()));
    // signal/slot connection: job auto-save
    QObject::connect(this, SIGNAL(dataChanged()), this, SLOT(save()));
    connect(_images, SIGNAL(countChanged(int)), this, SLOT(save()));
    for(size_t i = 0; i < _steps->rowCount(); i++)
    {
        QModelIndex id = _steps->index(i, 0);
        Step* step = _steps->data(id, StepModel::ModelDataRole).value<Step*>();
        connect(step->attributes(), SIGNAL(dataChanged(const QModelIndex&, const QModelIndex&)),
                this, SLOT(save()));
    }
}

void Job::setUrl(const QUrl& url)
{
    if(_url == url)
        return;
    _url = url;
    emit dataChanged();
}

void Job::setName(const QString& name)
{
    if(_name == name)
        return;
    _name = name;
    emit dataChanged();
}

void Job::setDate(const QDateTime& date)
{
    if(_date == date)
        return;
    _date = date;
    emit dataChanged();
}

void Job::setUser(const QString& user)
{
    if(_user == user)
        return;
    _user = user;
    emit dataChanged();
}

void Job::setCompletion(const float& completion)
{
    _completion = completion;
}

void Job::setStatus(const int& status)
{
    _status = status;
}

void Job::setThumbnail(const QUrl& thumbnail)
{
    _thumbnail = thumbnail;
}

void Job::setModelIndex(const QModelIndex& id)
{
    _modelIndex = id;
}

bool Job::load()
{
    // return in case the job url isn't valid
    if(!_url.isValid())
    {
        qCritical() << _name << ": malformed or empty URL '" << _url.toLocalFile() << "'";
        return false;
    }
    // return silently in case the directory doesn't exist yet
    QDir jobDirectory(_url.toLocalFile());
    if(!jobDirectory.exists())
        return false;
    // open a file handler
    QFile jobFile(jobDirectory.filePath("job.json"));
    if(!jobFile.open(QIODevice::ReadOnly))
    {
        qWarning() << _name << ": unable to read the job descriptor file" << jobFile.fileName();
        return false;
    }
    // read it and close the file handler
    QByteArray data = jobFile.readAll();
    jobFile.close();
    // parse data as JSON
    QJsonParseError parseError;
    QJsonDocument jsonDocument(QJsonDocument::fromJson(data, &parseError));
    if(parseError.error != QJsonParseError::NoError)
    {
        qWarning() << _name << ": malformed JSON file" << jobFile.fileName();
        return false;
    }
    // read job attributes
    QJsonObject json = jsonDocument.object();
    deserializeFromJSON(json);
    return true;
}

bool Job::save()
{
    // return in case the job is already started
    if(_status >= 0)
        return false;
    // build the JSON object for this job
    QJsonObject json;
    serializeToJSON(&json);

    // open a file handler
    QDir jobDirectory(_url.toLocalFile());
    QFile jobFile(jobDirectory.filePath("job.json"));
    if(!jobFile.open(QIODevice::WriteOnly | QIODevice::Text))
    {
        qWarning() << _name << ": unable to write the job descriptor file" << jobFile.fileName();
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
    // do not start an incomplete job
    if(_images->rowCount() < 2)
    {
        qCritical() << _name << ": insufficient number of sources";
        return false;
    }
    // do not start an invalid job
    if(!isPairValid())
    {
        qCritical() << _name << ": invalid initial pair";
        return false;
    }
    // define program path
    QString startCommand = std::getenv("MESHROOM_START_COMMAND");
    if(startCommand.isEmpty())
        startCommand = QCoreApplication::applicationDirPath() + "/scripts/job_start.py";
    // and add command arguments

    QString jobPath = _url.toLocalFile() + "/job.json";
    // run the process
    QProcess process;
    bool processStatus = false;
    if(local)
    {
      QString terminal = std::getenv("MESHROOM_TERMINAL");
      if(terminal.isEmpty())
        terminal = "xterm";

      QStringList arguments;
      // terminal args
      arguments << QString("-title") << _name+" - "+QString::fromStdString(std::to_string(_images->rowCount()))+" images\"" << "-hold" << "-e";
      // command line to execute
      arguments << startCommand << jobPath << "--engine=local";
      qint64 * pid = 0;
      QString workingDirectory;
      qInfo() << "Start command detached: " << terminal << " " << arguments.join(" ");
      processStatus = process.startDetached(terminal, arguments, workingDirectory, pid);
    }
    else
    {
      QStringList arguments;
      arguments << jobPath;
      qInfo() << "Start command: " << startCommand << " " << arguments.join(" ");
      process.start(startCommand, arguments);
      processStatus = process.waitForFinished();
    }

    if(!processStatus)
    {
        qCritical() << _name << ": unable to start job";
        return false;
    }

    // change the job status
    JobModel* model = qobject_cast<JobModel*>(parent());
    assert(model);
    model->setData(_modelIndex, 0, JobModel::StatusRole); // BLOCKED
    qInfo() << _name << ": job started";
    return true;
}

void Job::refresh()
{
    QFileInfo fileInfo(_url.toLocalFile() + "/job.json");
    if(!fileInfo.exists())
        return;
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
        qCritical() << _name << ": unable to update job status";
}

void Job::readProcessOutput(int exitCode, QProcess::ExitStatus exitStatus)
{
    QProcess* process = qobject_cast<QProcess*>(QObject::sender());
    JobModel* model = qobject_cast<JobModel*>(parent());
    assert(process);
    assert(model);
    // check exit status
    if(exitStatus != QProcess::NormalExit)
    {
        QString response(process->readAllStandardError());
        qCritical() << response;
        model->setData(_modelIndex, 4, JobModel::StatusRole); // ERROR
        return;
    }
    // parse standard output as JSON
    QJsonParseError parseError;
    QString response(process->readAllStandardOutput());
    QJsonDocument jsondoc(QJsonDocument::fromJson(response.toUtf8(), &parseError));
    if(parseError.error != QJsonParseError::NoError)
    {
        qCritical() << _name << ": invalid response - parse error";
        model->setData(_modelIndex, 4, JobModel::StatusRole); // ERROR
        return;
    }
    // retrieve & set job completion & status
    QJsonObject json = jsondoc.object();
    if(!json.contains("completion") || !json.contains("status"))
    {
        qCritical() << _name << ": invalid response - missing values";
        return;
    }
    model->setData(_modelIndex, json["completion"].toDouble(), JobModel::CompletionRole);
    model->setData(_modelIndex, json["status"].toInt(), JobModel::StatusRole);

    // case 0: // BLOCKED
    // case 1: // READY
    // case 2: // RUNNING
    // case 3: // DONE
    // case 4: // ERROR
    // case 5: // CANCELED
    // case 6: // PAUSED
}

void Job::selectPair()
{
    QModelIndex id;
    Step* step = nullptr;
    Attribute* initialPairAttribute = getAttribute(*this, "sfm", "initial_pair", id, &step);
    if(!step || !initialPairAttribute)
        return;
    // check if the current image pair still belongs to the job
    QVariantList pair = initialPairAttribute->value().toList();
    if((pair.count() > 0 && !isRegisteredImage(*this, QUrl::fromLocalFile(pair[0].toString()))) ||
       (pair.count() > 1 && !isRegisteredImage(*this, QUrl::fromLocalFile(pair[1].toString()))))
    {
        pair[0] = "";
        pair[1] = "";
        step->attributes()->setData(id, pair, AttributeModel::ValueRole);
    }
    // auto select the initial pair
    if(_images->rowCount() < 2)
        return;
    if(pair.count() > 0 && !QUrl::fromLocalFile(pair[0].toString()).isValid())
    {
        QModelIndex idA = _images->index(0, 0);
        pair[0] = _images->data(idA, ResourceModel::UrlRole).toUrl().toLocalFile();
        step->attributes()->setData(id, pair, AttributeModel::ValueRole);
    }
    if(pair.count() > 1 && !QUrl::fromLocalFile(pair[1].toString()).isValid())
    {
        QModelIndex idB = _images->index(1, 0);
        pair[1] = _images->data(idB, ResourceModel::UrlRole).toUrl().toLocalFile();
        step->attributes()->setData(id, pair, AttributeModel::ValueRole);
    }
}

void Job::selectThumbnail()
{
    JobModel* model = qobject_cast<JobModel*>(parent());
    if(!model)
        return;
    QModelIndex image0ID = _images->index(0, 0);
    model->setData(_modelIndex, _images->data(image0ID, ResourceModel::UrlRole),
                   JobModel::ThumbnailRole);
}

bool Job::isPairA(const QUrl& url)
{
    QModelIndex id;
    Step* step = nullptr;
    Attribute* initialPairAttribute = getAttribute(*this, "sfm", "initial_pair", id, &step);
    if(!step || !initialPairAttribute)
        return false;
    QVariantList pair = initialPairAttribute->value().toList();
    return (pair.count() > 0 && pair[0] == url.toLocalFile());
}

bool Job::isPairB(const QUrl& url)
{
    QModelIndex id;
    Step* step = nullptr;
    Attribute* initialPairAttribute = getAttribute(*this, "sfm", "initial_pair", id, &step);
    if(!step || !initialPairAttribute)
        return false;
    QVariantList pair = initialPairAttribute->value().toList();
    return (pair.count() > 1 && pair[1] == url.toLocalFile());
}

bool Job::isPairValid()
{
    QModelIndex id;
    Step* step = nullptr;
    Attribute* initialPairAttribute = getAttribute(*this, "sfm", "initial_pair", id, &step);
    if(!step || !initialPairAttribute)
        return false;
    QVariantList pair = initialPairAttribute->value().toList();
    return (pair.count() > 1 && QUrl::fromLocalFile(pair[0].toString()).isValid() &&
            QUrl::fromLocalFile(pair[1].toString()).isValid());
}

bool Job::isValid()
{
    QDir jobDirectory(_url.toLocalFile());
    QFile jobFile(jobDirectory.filePath("job.json"));
    return jobFile.exists();
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

void Job::deserializeFromJSON(const QJsonObject& obj)
{
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
}

} // namespace
