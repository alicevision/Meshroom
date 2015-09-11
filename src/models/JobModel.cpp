#include "JobModel.hpp"
#include "CameraModel.hpp"
#include "ResourceModel.hpp"
#include "io/JobsIO.hpp"
#include <QDir>
#include <QJsonObject>
#include <QJsonParseError>
#include <QDebug>
#include <cstdlib> // std::getenv

namespace mockup
{

JobModel::JobModel(QObject* parent)
    : QObject(parent)
    , _user(std::getenv("USER"))
{
}

const QUrl& JobModel::url() const
{
    return _url;
}

void JobModel::setUrl(const QUrl& url)
{
    if(url == _url)
        return;
    _url = url;
    if(_url.isValid())
        refresh();
    emit urlChanged();
}

const QString& JobModel::date() const
{
    return _date;
}

void JobModel::setDate(const QString& date)
{
    if(date == _date)
        return;
    _date = date;
    emit dateChanged();
}

const QString& JobModel::user() const
{
    return _user;
}

void JobModel::setUser(const QString& user)
{
    if(user == _user)
        return;
    _user = user;
    emit userChanged();
}

const QString& JobModel::note() const
{
    return _note;
}

void JobModel::setNote(const QString& note)
{
    if(note == _note)
        return;
    _note = note;
    emit noteChanged();
}

const QList<QObject*>& JobModel::cameras() const
{
    return _cameras;
}

const QList<QObject*>& JobModel::resources() const
{
    return _resources;
}

void JobModel::setResources(const QList<QObject*>& resources)
{
    if(resources == _resources)
        return;
    _resources = resources;
    setCamerasFromResources();
    emit resourcesChanged();
}

void JobModel::addResources(const QList<QUrl>& urls)
{
    // remove existing Urls from the list
    QList<QUrl> newUrls(urls);
    foreach(QObject* r, _resources)
    {
        ResourceModel* model = qobject_cast<ResourceModel*>(r);
        if(!model)
            continue;
        if(urls.contains(model->url()))
            newUrls.removeAll(model->url());
    }
    // add these new resources
    for(size_t i = 0; i < newUrls.length(); ++i)
    {
        if(ResourceModel::isValidUrl(newUrls[i]))
            _resources.append(new ResourceModel(newUrls[i], this));
    }
    setCamerasFromResources();
    emit resourcesChanged();
}

void JobModel::removeResources(const QList<QUrl>& urls)
{
    foreach(QObject* r, _resources)
    {
        ResourceModel* model = qobject_cast<ResourceModel*>(r);
        if(!model)
            continue;
        if(urls.contains(model->url()))
        {
            _resources.removeAll(model);
            if(_pairA == model->url())
                setPairA(QUrl());
            if(_pairB == model->url())
                setPairB(QUrl());
        }
    }
    setCamerasFromResources();
    emit resourcesChanged();
}

const QList<QString>& JobModel::steps() const
{
    return _steps;
}

void JobModel::setSteps(const QList<QString>& steps)
{
    if(steps == _steps)
        return;
    _steps = steps;
    emit stepsChanged();
}

const QUrl& JobModel::pairA() const
{
    return _pairA;
}

void JobModel::setPairA(const QUrl& url)
{
    if(url == _pairA)
        return;
    if(url.isValid() && url == _pairB)
    {
        qCritical("Set initial pair: please select 2 distinct images");
        return;
    }
    _pairA = url;
    emit pairAChanged();
    // try to add this resource in case its a new one
    addResources({url});
    // update resourceModels
    foreach(QObject* r, _resources)
    {
        ResourceModel* model = qobject_cast<ResourceModel*>(r);
        if(!model)
            continue;
        model->setIsPairImageA(model->url() == _pairA);
    }
}

const QUrl& JobModel::pairB() const
{
    return _pairB;
}

void JobModel::setPairB(const QUrl& url)
{
    if(url == _pairB)
        return;
    if(url.isValid() && url == _pairA)
    {
        qCritical("Set initial pair: please select 2 distinct images");
        return;
    }
    _pairB = url;
    emit pairBChanged();
    // try to add this resource in case its a new one
    addResources({url});
    // update resourceModels
    foreach(QObject* r, _resources)
    {
        ResourceModel* model = qobject_cast<ResourceModel*>(r);
        if(!model)
            continue;
        model->setIsPairImageB(model->url() == _pairB);
    }
}

const int& JobModel::describerPreset() const
{
    return _describerPreset;
}

void JobModel::setDescriberPreset(const int& threshold)
{
    if(threshold == _describerPreset)
        return;
    _describerPreset = threshold;
    emit describerPresetChanged();
}

const int& JobModel::meshingScale() const
{
    return _meshingScale;
}

void JobModel::setMeshingScale(const int& scale)
{
    if(scale == _meshingScale)
        return;
    _meshingScale = scale;
    emit meshingScaleChanged();
}

const float& JobModel::completion() const
{
    return _completion;
}

void JobModel::setCompletion(const float& completion)
{
    if(completion == _completion)
        return;
    _completion = completion;
    emit completionChanged();
}

const int& JobModel::status() const
{
    return _status;
}

void JobModel::setStatus(const int& status)
{
    if(status == _status)
        return;
    _status = status;
    emit statusChanged();
}

QUrl JobModel::buildUrl() const
{
    QDir dir(_url.toLocalFile());
    return QUrl::fromLocalFile(dir.absoluteFilePath("build"));
}

QUrl JobModel::matchUrl() const
{
    QDir dir(_url.toLocalFile());
    return QUrl::fromLocalFile(dir.absoluteFilePath("build/matches"));
}

void JobModel::autoSaveON()
{
    connect(this, SIGNAL(urlChanged()), this, SLOT(save()));
    connect(this, SIGNAL(dateChanged()), this, SLOT(save()));
    connect(this, SIGNAL(userChanged()), this, SLOT(save()));
    connect(this, SIGNAL(noteChanged()), this, SLOT(save()));
    connect(this, SIGNAL(camerasChanged()), this, SLOT(save()));
    connect(this, SIGNAL(resourcesChanged()), this, SLOT(save()));
    connect(this, SIGNAL(stepsChanged()), this, SLOT(save()));
    connect(this, SIGNAL(pairAChanged()), this, SLOT(save()));
    connect(this, SIGNAL(pairBChanged()), this, SLOT(save()));
    connect(this, SIGNAL(describerPresetChanged()), this, SLOT(save()));
    connect(this, SIGNAL(meshingScaleChanged()), this, SLOT(save()));
}

bool JobModel::save()
{
    return JobsIO::save(*this);
}

void JobModel::start()
{
    JobsIO::start(*this, _process);
}

void JobModel::stop()
{
    JobsIO::stop(*this, _process);
}

void JobModel::refresh()
{
    JobsIO::status(*this, _process);
}

void JobModel::readProcessOutput(int exitCode, QProcess::ExitStatus exitStatus)
{
    QObject::disconnect(&_process, SIGNAL(finished(int, QProcess::ExitStatus)), this,
                        SLOT(readProcessOutput(int, QProcess::ExitStatus)));

    if(exitStatus != QProcess::NormalExit)
    {
        QString response(_process.readAllStandardError());
        qCritical() << response;
    }

    // parse standard output as JSON
    QJsonParseError parseError;
    QString response(_process.readAllStandardOutput());
    QJsonDocument jsondoc(QJsonDocument::fromJson(response.toUtf8(), &parseError));
    if(parseError.error != QJsonParseError::NoError)
    {
        qCritical("Invalid response: parse error");
        return;
    }

    // retrieve job completion
    QJsonObject json = jsondoc.object();
    if(!json.contains("completion") || !json.contains("status"))
    {
        qCritical("Invalid response: missing values");
        return;
    }

    // set job completion & status
    setCompletion(json["completion"].toDouble());
    setStatus(json["status"].toInt());

    // case 0: // BLOCKED
    // case 1: // READY
    // case 2: // RUNNING
    // case 3: // DONE
    // case 4: // ERROR
    // case 5: // CANCELED
    // case 6: // PAUSED
}

// static
QString JobModel::describerPresetString(const int& describerId)
{
    switch(describerId)
    {
        case 0:
            return "NORMAL";
        case 2:
            return "ULTRA";
        case 1:
        default:
            return "HIGH";
    }
}

// static
int JobModel::describerPresetId(const QString& describerString)
{
    if(describerString == "NORMAL")
        return 0;
    if(describerString == "ULTRA")
        return 2;
    else // HIGH
        return 1;
}

// private
void JobModel::setCamerasFromResources()
{
    QObjectList cameras;
    foreach(QObject* r, resources())
    {
        ResourceModel* resource = qobject_cast<ResourceModel*>(r);
        cameras.append(new CameraModel(resource->url(), this));
    }
    _cameras = cameras;
    emit camerasChanged();
}

} // namespace
