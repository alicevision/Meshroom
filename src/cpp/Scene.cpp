#include "Scene.hpp"
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>
#include <QFileInfo>
#include <QDir>
#include <QDebug>
#include <cstdlib> // std::getenv

#define LOGID (QString("[scene:%1]").arg(_name)).toStdString().c_str()

namespace meshroom
{

Scene::Scene(QObject* parent, const QUrl& url)
    : QObject(parent)
    , _graph(new Graph(this))
{
    // callbacks
    auto setDirty_CB = [this]()
    {
        setDirty(true);
    };
    auto setName_CB = [this]()
    {
        if(!_url.isEmpty())
            setName(_url.fileName().replace(".meshroom", ""));
    };

    // connections
    connect(this, &Scene::urlChanged, this, setName_CB);
    connect(this, &Scene::nameChanged, this, setDirty_CB);
    connect(this, &Scene::thumbnailChanged, this, setDirty_CB);

    // initialization
    reset();
    setUrl(url);
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

void Scene::setDirty(const bool& dirty)
{
    if(_dirty == dirty)
        return;
    _dirty = dirty;
    Q_EMIT dirtyChanged();
}

bool Scene::load()
{
    // check if the file exists
    if(!QFileInfo::exists(_url.toLocalFile()))
    {
        qCritical() << LOGID << "can't open file " << _url.toLocalFile();
        return false;
    }

    // open a file handler
    QFile file(_url.toLocalFile());
    if(!file.open(QIODevice::ReadOnly))
    {
        qCritical() << LOGID << "can't open file " << _url.toLocalFile();
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
        qCritical() << LOGID << "malformed JSON file " << _url.toLocalFile();
        return false;
    }

    // deserialize the JSON document
    deserializeFromJSON(document.object());

    // reset the dirty flag
    setDirty(false);

    // refresh node statuses
    _graph->startWorker(Graph::BuildMode::PREPARE);

    return true;
}

bool Scene::save()
{
    // check if the URL is valid
    if(!_url.isValid())
    {
        qCritical() << LOGID << "invalid URL " << _url.toLocalFile();
        return false;
    }

    // build the JSON object
    QJsonObject json = serializeToJSON();

    // open a file handler
    QFile file(_url.toLocalFile());
    if(!file.open(QIODevice::WriteOnly | QIODevice::Text))
    {
        qWarning() << LOGID << "unable to write file " << _url.toLocalFile();
        return false;
    }

    // write & close the file handler
    QJsonDocument document(json);
    file.write(document.toJson());
    file.close();

    // reset the dirty flag
    setDirty(false);
    return true;
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
    setUrl(QUrl());
    setName("untitled");
    setUser(std::getenv("USER"));
    setDate(QDateTime::currentDateTime());
    setDirty(false);
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
