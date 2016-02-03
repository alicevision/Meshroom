#include "Project.hpp"
#include <QJsonDocument>
#include <QJsonObject>
#include <QDir>
#include <QDebug>

#define LOGID (QString("[project:%1]").arg(_name)).toStdString().c_str()

namespace meshroom
{

Project::Project(const QUrl& url)
    : _url(url)
    , _name(url.fileName())
    , _jobs(new JobModel(this))
    , _proxy(new QSortFilterProxyModel(this))
{
    if(!_url.isValid())
        return;
    // setup proxy filters
    _proxy->setSourceModel(_jobs);
    _proxy->setFilterRole(JobModel::NameRole);
    // load project settings
    load();
    // populate with project's jobs
    populate();
    // signal/slot connection: project auto-save
    QObject::connect(this, SIGNAL(nameChanged()), this, SLOT(save()));
}

void Project::setName(const QString& name)
{
    if(_name == name)
        return;
    _name = name;
    emit nameChanged();
    emit dataChanged(_modelIndex, _modelIndex);
}

void Project::setModelIndex(const QModelIndex& id)
{
    _modelIndex = id;
}

bool Project::load()
{
    // open a file handler
    QDir projectDirectory(_url.toLocalFile());
    QFile projectFile(projectDirectory.filePath("project.json"));
    if(!projectFile.open(QIODevice::ReadOnly))
    {
        qInfo() << LOGID << "unable to read the project descriptor file" << projectFile.fileName();
        return false;
    }
    // read it and close the file handler
    QByteArray data = projectFile.readAll();
    projectFile.close();
    // parse data as JSON
    QJsonParseError parseError;
    QJsonDocument jsonDocument(QJsonDocument::fromJson(data, &parseError));
    if(parseError.error != QJsonParseError::NoError)
    {
        qWarning() << LOGID << "malformed JSON file" << projectFile.fileName();
        return false;
    }
    // read project attributes
    QJsonObject json = jsonDocument.object();
    deserializeFromJSON(json);
    return true;
}

bool Project::save()
{
    if(!_url.isValid())
        return false;
    // build the JSON object for this project
    QJsonObject json;
    serializeToJSON(&json);
    // open a file handler
    QDir projectDirectory(_url.toLocalFile());
    QFile projectFile(projectDirectory.filePath("project.json"));
    if(!projectFile.open(QIODevice::WriteOnly | QIODevice::Text))
    {
        qWarning() << LOGID << "unable to write the project descriptor file"
                   << projectFile.fileName();
        return false;
    }
    // write & close the file handler
    QJsonDocument jsonDocument(json);
    projectFile.write(jsonDocument.toJson());
    projectFile.close();
    return true;
}

void Project::setFilterRegexp(const QString& regexp)
{
    _proxy->setFilterRegExp(QRegExp(regexp));
}

void Project::populate()
{
    QDir dir(_url.toLocalFile());
    dir.cd("reconstructions");
    // list sub-directories to retrieve all existing jobs
    QStringList jobs = dir.entryList(QDir::Dirs | QDir::NoDotAndDotDot);
    for(size_t i = 0; i < jobs.length(); ++i)
    {
        Job* job = new Job(this);
        if(job->load(QUrl::fromLocalFile(dir.absoluteFilePath(jobs[i]))))
            _jobs->addJob(job);
    }
    // we should have at least one job
    if(_jobs->rowCount() <= 0)
    {
        Job* job = new Job(this);
        _jobs->addJob(job);
    }
}

void Project::serializeToJSON(QJsonObject* obj) const
{
    if(!obj)
        return;
    obj->insert("name", _name);
}

void Project::deserializeFromJSON(const QJsonObject& obj)
{
    if(!obj.contains("name"))
        return;
    _name = obj["name"].toString();
}

} // namespace
