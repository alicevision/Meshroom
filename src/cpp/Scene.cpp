#include "Scene.hpp"
#include "Commands.hpp"
#include "Application.hpp"
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>
#include <QFileInfo>
#include <QDir>
#include <cstdlib> // std::getenv

#define LOGID qPrintable(QString("[scene:%1]").arg(_name))

namespace meshroom
{

const std::string Scene::DEFAULT_CACHE_FOLDERNAME = ".meshroom_cache";

Scene::Scene()
    : _undoStack(new UndoStack(this))
{
}

Scene::Scene(QObject* parent, const QUrl& url)
    : QObject(parent)
    , _undoStack(new UndoStack(this))
{

    // callbacks
    auto setDefault_CB = [this]()
    {
        if(!_url.isValid())
            return;
        // compute default name
        setName(_url.fileName().replace(".meshroom", ""));
        // compute default cacheUrl
        for(auto* graph : _graphs)
        {
            graph->coreEnvironment().push(dg::Environment::Key::SCENE_FILE,
                                          _url.toLocalFile().toStdString());
        }
    };

    // connections
    connect(this, &Scene::urlChanged, this, setDefault_CB);
    connect(this, &Scene::cacheUrlChanged, this, [&](){
        // update graphs cache urls
        for(auto* graph : _graphs)
            graph->setCacheUrl(_cacheUrl);
    });

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

void Scene::setCacheUrl(const QUrl& cacheUrl)
{
    if(cacheUrl == _cacheUrl)
        return;
    _cacheUrl = cacheUrl;
    Q_EMIT cacheUrlChanged();
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
    clear();

    if(url.isEmpty())
    {
        reset();
        return false;
    }

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

    // clear the undostack
    _undoStack->clear();

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
    _undoStack->beginMacro("Import Graph");
    _graph->deserializeFromJSON(document.object());
    _undoStack->endMacro();

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
    QDir baseDir = QFileInfo(_url.toLocalFile()).absoluteDir();
    setCacheUrl(QUrl::fromLocalFile(
                    baseDir.absoluteFilePath(Scene::DEFAULT_CACHE_FOLDERNAME.c_str())
                    ));
    return save();
}

void Scene::erase()
{
    QFileInfo file(_url.toLocalFile());
    QDir dir = file.dir();
    if(dir.exists())
        dir.removeRecursively();
}

void Scene::clear()
{
    for(auto* graph : _graphs)
    {
        graph->deleteLater();
    }
    _graphs.clear();
    _graph = nullptr;
    _undoStack->clear();
}

void Scene::reset()
{
    clear();
    setUrl(QUrl());
    setName("untitled");
    setUser(std::getenv("USER"));
    setDate(QDateTime::currentDateTime());
    addGraph(true);
    undoStack()->clear();
}

void Scene::addGraph(bool makeCurrent)
{
    _undoStack->beginMacro("Add Graph");
    _undoStack->tryAndPush(new AddGraphCmd(this));
    if(makeCurrent)
        setGraph(_graphs.last());
    _undoStack->endMacro();
}

void Scene::duplicateGraph(Graph *graph, bool makeCurrent)
{
    _undoStack->beginMacro("Duplicate Graph");
    _undoStack->tryAndPush(new AddGraphCmd(this, graph->serializeToJSON()));
    if(makeCurrent)
        setGraph(_graphs.last());
    _undoStack->endMacro();
}

void Scene::deleteGraph(Graph *graph)
{
    _undoStack->beginMacro("Delete Graph");
    _undoStack->tryAndPush(new DeleteGraphCmd(this, _graphs.indexOf(graph)));
    _undoStack->endMacro();
}

void Scene::setGraph(Graph *graph)
{
    if(graph == _graph)
        return;
    _graph = graph;
    Q_EMIT graphChanged();
}

Graph* Scene::createAndAddGraph(bool makeCurrent, const QJsonObject& graphdesc, int idx)
{
    Graph* g = new Graph(this);

    auto executable = dg::Environment::system("MESHROOM_COMMAND_EXECUTABLE");
    if(!executable.empty())
        g->coreEnvironment().push(dg::Environment::Key::COMMAND_EXECUTABLE, executable);
    if(_cacheUrl.isValid())
        g->setCacheUrl(_cacheUrl);
    if(!graphdesc.isEmpty())
        g->deserializeFromJSON(graphdesc, false);
    addGraph(g, idx);
    if(makeCurrent)
        setGraph(g);
    return g;
}

void Scene::addGraph(Graph *graph, int idx)
{
    if(idx < 0)
        _graphs.append(graph);
    else
        _graphs.insert(idx, graph);
}

void Scene::doDeleteGraph(Graph *graph)
{
    // store graph's index and remove it from the scene
    const int idx = currentGraphIdx();
    _graphs.remove(graph);
    // if graph was the current graph, chose another one
    // based on its index
    if(_graph == graph)
        setGraph(_graphs.at(std::min(idx, _graphs.count() - 1)));
    // delete the graph
    graph->deleteLater();
}

QJsonObject Scene::serializeToJSON() const
{
    QJsonObject obj;
    obj.insert("date", QJsonValue::fromVariant(_date));
    obj.insert("user", _user);
    obj.insert("cacheUrl", _cacheUrl.toLocalFile());
    QJsonArray array;
    for(const auto* g : _graphs)
        array.append(g->serializeToJSON());
    obj.insert("graphs", array);
    return obj;
}

void Scene::deserializeFromJSON(const QJsonObject& obj)
{
    QJsonArray graphs;
    if(obj.contains("cacheUrl"))
        setCacheUrl(QUrl::fromLocalFile(obj.value("cacheUrl").toString()));

    // Compatibility with older scenes with only one graph
    if(obj.contains("graph"))
        graphs.append(obj.value("graph"));
    else
        graphs = obj.value("graphs").toArray();

    for(auto graphObj : graphs)
    {
        Graph* g = createAndAddGraph(false);
        g->deserializeFromJSON(graphObj.toObject());
    }
    setGraph(_graphs.last()); //TODO: chose better

    setUser(obj.value("user").toString());
}

} // namespace
