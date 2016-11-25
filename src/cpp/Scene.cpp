#include "Scene.hpp"
#include "Commands.hpp"
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>
#include <QFileInfo>
#include <QDir>
#include <QDebug>
#include <cstdlib> // std::getenv

#define LOGID qPrintable(QString("[scene:%1]").arg(_name))

namespace meshroom
{

Scene::Scene()
    : _undoStack(new UndoStack(this))
    , _graph(new Graph)
{
}

Scene::Scene(QObject* parent, const QUrl& url)
    : QObject(parent)
    , _undoStack(new UndoStack(this))
    , _graph(new Graph(this))
{
    // callbacks
    auto setDefault_CB = [this]()
    {
        if(!_url.isValid())
            return;
        // compute default name
        if(_name.isEmpty() || _name == "untitled")
            setName(_url.fileName().replace(".meshroom", ""));
        // compute default cacheUrl
        if(!_graph->cacheUrl().isValid())
        {
            QDir baseDir = QFileInfo(_url.toLocalFile()).absoluteDir();
            _graph->setCacheUrl(QUrl::fromLocalFile(baseDir.absoluteFilePath(_name)));
        }
    };

    // connections
    connect(this, &Scene::urlChanged, this, setDefault_CB);

    // load
    load(url);
}

void Scene::setUrl(const QUrl& url)
{
    if(_url == url)
        return;
    _url = url;
    Q_EMIT urlChanged();
}

void Scene::setName(const QString& name)
{
    if(_name == name)
        return;
    _name = name;
    Q_EMIT nameChanged();
}

void Scene::setDate(const QDateTime& date)
{
    if(_date == date)
        return;
    _date = date;
    Q_EMIT dateChanged();
}

void Scene::setUser(const QString& user)
{
    if(_user == user)
        return;
    _user = user;
    Q_EMIT userChanged();
}

void Scene::setThumbnail(const QUrl& thumbnail)
{
    if(_thumbnail == thumbnail)
        return;
    _thumbnail = thumbnail;
    Q_EMIT thumbnailChanged();
}

bool Scene::load(const QUrl& url)
{
    // reset
    reset();

    if(url.isEmpty())
        return false;

    // open a file handler
    QFile file(url.toLocalFile());
    if(!file.open(QIODevice::ReadOnly))
    {
        qCritical() << "can't open scene file" << url.toLocalFile();
        return false;
    }

    // set url
    setUrl(url);

    // read data and close the file handler
    QByteArray data = file.readAll();
    file.close();

    // parse data as JSON
    QJsonParseError error;
    QJsonDocument document(QJsonDocument::fromJson(data, &error));
    if(error.error != QJsonParseError::NoError)
    {
        qCritical() << LOGID << "malformed JSON file" << _url.toLocalFile();
        return false;
    }

    // deserialize the JSON document
    deserializeFromJSON(document.object());

    // add to recent-file list
    Application* application = qobject_cast<Application*>(parent());
    if(application)
        application->settings()->addRecentFile(url);

    // mark the undo stack as clean
    _undoStack->setClean();

    return true;
}

bool Scene::import(const QUrl& url)
{
    if(url.isEmpty())
        return false;

    // open a file handler
    QFile file(url.toLocalFile());
    if(!file.open(QIODevice::ReadOnly))
    {
        qCritical() << LOGID << "can't import file" << url.toLocalFile();
        return false;
    }

    // read data and close the file handler
    QByteArray data = file.readAll();
    file.close();

    // parse data as JSON
    QJsonParseError error;
    QJsonDocument document(QJsonDocument::fromJson(data, &error));
    if(error.error != QJsonParseError::NoError)
    {
        qCritical() << LOGID << "malformed JSON file" << _url.toLocalFile();
        return false;
    }

    // read graph data
    QJsonObject obj = document.object();
    _graph->deserializeFromJSON(obj.value("graph").toObject());

    return true;
}

bool Scene::save()
{
    // check if the URL is valid
    if(!_url.isValid())
    {
        qCritical() << LOGID << "invalid URL" << _url.toLocalFile();
        return false;
    }

    // build the JSON object
    QJsonObject json = serializeToJSON();

    // open a file handler
    QFile file(_url.toLocalFile());
    if(!file.open(QIODevice::WriteOnly | QIODevice::Text))
    {
        qWarning() << LOGID << "unable to write file" << _url.toLocalFile();
        return false;
    }

    // write & close the file handler
    QJsonDocument document(json);
    file.write(document.toJson());
    file.close();

    // mark the undo stack as clean
    _undoStack->setClean();

    return true;
}

bool Scene::saveAs(const QUrl& url)
{
    // check if the URL is valid
    if(!url.isValid())
    {
        qCritical() << LOGID << "invalid URL" << url.toLocalFile();
        return false;
    }

    setUrl(url);
    return save();
}

void Scene::erase()
{
    QFileInfo file(_url.toLocalFile());
    QDir dir = file.dir();
    if(dir.exists())
        dir.removeRecursively();
}

void Scene::reset()
{
    _graph->clear();
    _graph->setCacheUrl(QUrl());
    setUrl(QUrl());
    setName("untitled");
    setUser(std::getenv("USER"));
    setDate(QDateTime::currentDateTime());
}

QJsonObject Scene::serializeToJSON() const
{
    QJsonObject obj;
    obj.insert("date", QJsonValue::fromVariant(_date));
    obj.insert("user", _user);
    obj.insert("graph", _graph->serializeToJSON());
    return obj;
}

void Scene::deserializeFromJSON(const QJsonObject& obj)
{
    _graph->deserializeFromJSON(obj.value("graph").toObject());
    setUser(obj.value("user").toString());
}

} // namespace
