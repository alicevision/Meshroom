#include "JobsIO.hpp"
#include "models/Job.hpp"
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>
#include <QFile>
#include <QDir>

namespace meshroom
{

void JobsIO::load(Job& job)
{
    if(!job.url().isValid())
    {
        qCritical("Loading job : invalid URL (malformed or empty URL)");
        return;
    }

    QDir dir(job.url().toLocalFile());
    if(!dir.exists())
        return;

    job.setDate(QDateTime::fromString(job.url().fileName(), "yyyyMMdd_HHmmss"));

    // load the JSON file
    QFile file(dir.filePath("job.json"));
    if(!file.open(QIODevice::ReadOnly))
    {
        qCritical("Loading job : unable to open JSON file");
        return;
    }

    // read it and close the file handler
    QByteArray data = file.readAll();
    file.close();

    // parse data as JSON
    QJsonParseError parseError;
    QJsonDocument jsondoc(QJsonDocument::fromJson(data, &parseError));
    if(parseError.error != QJsonParseError::NoError)
    {
        qCritical("Loading job : malformed JSON file");
        return;
    }

    QJsonObject json = jsondoc.object();
    if(json.contains("user"))
        job.setUser(json["user"].toString());
    if(json.contains("name"))
        job.setName(json["name"].toString());
    QJsonArray resourceArray = json["resources"].toArray();
    QObjectList resources;
    for(int i = 0; i < resourceArray.count(); ++i)
    {
        Resource* r = new Resource(QUrl::fromLocalFile(resourceArray.at(i).toString()));
        job.images()->addResource(r);
    }
    QJsonObject stepsObject = json["steps"].toObject();
    for(size_t i = 0; i < job.steps()->rowCount(); i++)
    {
        QModelIndex id = job.steps()->index(i, 0);
        Step* step = job.steps()->data(id, StepModel::ModelDataRole).value<Step*>();
        if(!step)
            continue;
        step->deserializeFromJSON(stepsObject);
    }
}

bool JobsIO::save(Job& job)
{
    if(job.status() >= 0) // job already started
        return false;

    // build the JSON object
    QJsonObject jobObj;
    QJsonObject pathsObject;
    pathsObject["build"] = job.url().toLocalFile() + "/build";
    pathsObject["match"] = job.url().toLocalFile() + "/build/matches";
    QJsonArray resourceArray;
    for(size_t i = 0; i < job.images()->rowCount(); i++)
    {
        QModelIndex id = job.images()->index(i, 0);
        Resource* resource =
            job.images()->data(id, ResourceModel::ModelDataRole).value<Resource*>();
        if(resource)
            resource->serializeToJSON(&resourceArray);
    }
    QJsonObject stepsObject;
    for(size_t i = 0; i < job.steps()->rowCount(); i++)
    {
        QModelIndex id = job.steps()->index(i, 0);
        Step* step = job.steps()->data(id, StepModel::ModelDataRole).value<Step*>();
        if(step)
            step->serializeToJSON(&stepsObject);
    }
    jobObj.insert("date", QJsonValue::fromVariant(job.date()));
    jobObj.insert("user", job.user());
    jobObj.insert("name", job.name());
    jobObj.insert("paths", pathsObject);
    jobObj.insert("resources", resourceArray);
    jobObj.insert("steps", stepsObject);

    // create filesystem structure
    QDir dir;
    if(!dir.mkpath(job.url().toLocalFile()))
    {
        qCritical("Saving job: unable to create directory structure (job url)");
        return false;
    }
    if(!dir.mkpath(job.url().toLocalFile() + "/build"))
    {
        qCritical("Saving job: unable to create directory structure (build url)");
        return false;
    }
    if(!dir.mkpath(job.url().toLocalFile() + "/build/matches"))
    {
        qCritical("Saving job: unable to create directory structure (match url)");
        return false;
    }

    // open a file handler
    QDir rootDir(job.url().toLocalFile());
    QFile file(rootDir.filePath("job.json"));
    if(!file.open(QIODevice::WriteOnly | QIODevice::Text))
    {
        qCritical("Saving job: unable to write the job descriptor file");
        return false;
    }

    // write & close file
    QJsonDocument jsonDoc(jobObj);
    file.write(jsonDoc.toJson());
    file.close();

    return true;
}

} // namespace
