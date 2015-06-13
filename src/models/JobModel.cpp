#include "JobModel.hpp"
#include "CameraModel.hpp"
#include "ResourceModel.hpp"
#include <QDir>
#include <cstdlib>

namespace mockup
{

JobModel::JobModel(const QUrl& url, QObject* parent)
    : QObject(parent)
    , _url(url)
    , _user(std::getenv("USER"))
    , _io(*this)
    , _error(ERR_NOERROR)
{
    loadFromDisk();
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
    loadFromDisk();
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

void JobModel::setCameras(const QList<QObject*>& cameras)
{
    if(cameras == _cameras)
        return;
    _cameras = cameras;
    emit camerasChanged();
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
    for(size_t i = 0; i < urls.length(); ++i)
    {
        if(ResourceModel::isValidUrl(urls[i]))
            _resources.append(new ResourceModel(urls[i], this));
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
            _resources.removeAll(model);
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

const QList<QUrl>& JobModel::pair() const
{
    return _pair;
}

void JobModel::setPair(const QList<QUrl>& pair)
{
    if(pair == _pair)
        return;
    _pair = pair;
    emit pairChanged();
}

bool JobModel::addPairElement(const QUrl& url)
{
    if(_pair.count() >= 2)
        return false;
    _pair.append(url);
    emit pairChanged();
    return true;
}

bool JobModel::removePairElement(const QUrl& url)
{
    int removed = _pair.removeAll(url);
    if(removed <= 0)
        return false;
    emit pairChanged();
    return true;
}

const float& JobModel::peakThreshold() const
{
    return _peakThreshold;
}

void JobModel::setPeakThreshold(const float& threshold)
{
    if(threshold == _peakThreshold)
        return;
    _peakThreshold = threshold;
    emit peakThresholdChanged();
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

const bool& JobModel::running() const
{
    return _running;
}

void JobModel::setRunning(const bool& running)
{
    if(running == _running)
        return;
    _running = running;
    emit runningChanged();
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

JobModel::ERROR_TYPE JobModel::error() const
{
    return _error;
}

QString JobModel::errorString() const
{
    switch(_error)
    {
        case ERR_INVALID_URL:
            return "Invalid URL";
        case ERR_INVALID_DESCRIPTOR:
            return "Invalid descriptor file";
        case ERR_MALFORMED_DESCRIPTOR:
            return "Malformed descriptor file";
        case ERR_SOURCE_LACK:
            return "Insufficient number of sources";
        case ERR_INVALID_INITIAL_PAIR:
            return "Invalid initial pair";
        case ERR_NOERROR:
            return "";
    }
    return "";
}

void JobModel::setError(ERROR_TYPE e)
{
    if(_error == e)
        return;
    _error = e;
}

void JobModel::start()
{
    _io.start();
}

void JobModel::stop()
{
    _io.stop();
}

void JobModel::refresh()
{
    _io.refresh();
}

bool JobModel::loadFromDisk()
{
    if(!_io.load())
        return false;
    refresh();
    return true;
}

bool JobModel::saveToDisk() const
{
    return _io.save();
}

// private
void JobModel::setCamerasFromResources()
{
    QObjectList cameras;
    foreach(QObject* r, resources())
    {
        ResourceModel* resource = qobject_cast<ResourceModel*>(r);
        if(resource->isDir())
        {
            QDir dir(resource->url().toLocalFile());
            QStringList list = dir.entryList(ResourceModel::validFileExtensions());
            for(int i = 0; i < list.size(); ++i)
                cameras.append(
                    new CameraModel(QUrl::fromLocalFile(dir.absoluteFilePath(list[i])), this));
            continue;
        }
        cameras.append(new CameraModel(resource->url(), this));
    }
    setCameras(cameras);
}

} // namespace
