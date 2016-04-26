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

const QString cameraModelTooltip = R"(
Camera model

Values:
    - Pinhole: simple camera without a lens
    - Radial1: lens with radial distortion (1 parameter)
    - Radial3 (default): lens with radial distortion (3 parameters)
    - Brown: lens with radial and tangential distortion (3 radial and 2 tangential parameters)
    - Fisheye: ultra wide-angle lens that produces strong visual distortion intended to create a wide panoramic or hemispherical image
)";
const QString densityTooltip = R"(
Density of features per image

It's important to use an high value if your dataset contains:
    - weakly textured surfaces (like indoor)
    - if you have few pictures (<50)
    - have a poor overlap
    - wide baseline

Values:
    - LOW: Useful to get a rapid overview on large (>500 images) datasets with many overlapping images
    - MEDIUM: To get a fast reconstruction
    - NORMAL: Good value for most datasets with more than 200 images
    - HIGH (default): Good value for small datasets (<200 images)
    - ULTRA: Good value for very small datasets (<50 images) or for larger datasets with challenging conditions
)";
const QString featureTypeTooltip = R"(
Feature type

Values:
    - SIFT (default): Scale-invariant feature transform is an algorithm in computer vision to detect and describe local features in images.
    - CCTAG3: CCTAG markers with 3 crowns
    - SIFT_CCTAG3: Use both CCTag and SIFT.
)";
const QString maxMatchesTooltip = R"(
Maximum matches per image pair

Limit the number of matches per image pair.
Small values (100) generates fast SfM and coarse 3D reconstruction, high values (2000) generates finer, more accurate 3D reconstructions with high density point clouds at the cost of high computational times.
)";
const QString methodTooltip = R"(
Method

Values:
    - BRUTEFORCEL2: L2 BruteForce matching
    - ANNL2 (default): L2 Approximate Nearest Neighbor matching
    - CASCADEHASHINGL2: L2 Cascade Hashing matching.
    - FASTCASCADEHASHINGL2: L2 Cascade Hashing with precomputed hashed regions (faster than CASCADEHASHINGL2 but use more memory)
)";
const QString guidedMatchingTooltip = R"(
Guided Matching

Improve matches density by using geometric constrain to deal with repetitive or ambiguous patterns.
)";
const QString initialPairTooltip = R"(
Initial pair

This image pair can be choosed automatically but you can choose it manually to improve the quality by selecting a good pair in the center of interest of the scene.
The goal is to maximize the overlap between the 2 images (the framing should be quite the same) but with an angle between 10° to 30° regarding the surface you are shooting.
)";
const QString minimumTrackLengthTooltip = R"(
Minimum track length

Minimum number of images associated to a point.
)";
const QString scaleTooltip = R"(
Meshing scale

Input images downscale factor for meshing. 2 is the recommanded value in most cases.
)";

const QString enableMeshingTooltip = R"(
Enable meshing

Enable generation of meshes.
)";

const QString undistortTooltip = R"(
Enable undistort

Export undistorted images from known camera parameter intrinsic
)";

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
        QUrl imgUrl = images->data(id, ResourceModel::UrlRole).toUrl();
        if(url.matches(imgUrl, QUrl::RemoveScheme))
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
}

void Job::setCompletion(const float& completion)
{
    if(_completion == completion)
        return;
    _completion = completion;
    emit completionChanged();
}

void Job::setStatus(const StatusType& status)
{
    if(_status == status)
        return;
    _status = status;
    emit statusChanged();
}

void Job::setThumbnail(const QUrl& thumbnail)
{
    if(_thumbnail == thumbnail)
        return;
    _thumbnail = thumbnail;
    emit thumbnailChanged();
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
        qWarning() << LOGID << "no descriptor file";
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
    QUrl pairA = QUrl::fromLocalFile(pair[0].toString());
    QUrl pairB = QUrl::fromLocalFile(pair[1].toString());
    return (pairA.isEmpty() && pairB.toString().isEmpty()) ||
           (isRegisteredImage(*this, pairA) && isRegisteredImage(*this, pairB));
}

void Job::createDefaultGraph()
{
    // image listing
    // Step* step = new Step("image_listing");
    // Attribute* att = new Attribute();
    // att->setType(2); // combo
    // att->setKey("cameraModel");
    // att->setName("camera model");
    // att->setTooltip(cameraModelTooltip);
    // att->setValue("Radial3");
    // att->setOptions(QStringList({"Pinhole", "Radial1", "Radial3", "Brown", "Fisheye"}));
    // step->attributes()->addAttribute(att);
    // _steps->addStep(step);

    // feature detection
    Step* step = new Step("feature_detection");
    Attribute* att = new Attribute();
    att->setType(2); // combo
    att->setKey("describerPreset");
    att->setName("density");
    att->setTooltip(densityTooltip);
    att->setValue("Normal");
    att->setOptions(QStringList({"Normal", "High", "Ultra"}));
    step->attributes()->addAttribute(att);

    att = new Attribute();
    att->setType(2); // combo
    att->setKey("method");
    att->setName("feature type");
    att->setTooltip(featureTypeTooltip);
    att->setValue("SIFT");
    att->setOptions(QStringList({"SIFT", "CCTAG3", "SIFT_CCTAG3"}));
    step->attributes()->addAttribute(att);
    _steps->addStep(step);

    // matching
    // step = new Step("matching");
    // att = new Attribute();
    // att->setType(1); // slider
    // att->setKey("maxMatches");
    // att->setName("max matches per image pair");
    // att->setTooltip(maxMatchesTooltip);
    // att->setValue(500);
    // att->setMin(100);
    // att->setMax(10000);
    // att->setStep(1);
    // step->attributes()->addAttribute(att);

    // att = new Attribute();
    // att->setType(2); // combo
    // att->setKey("method");
    // att->setName("method");
    // att->setTooltip(methodTooltip);
    // att->setValue("ANNL2");
    // att->setOptions(QStringList({"BRUTEFORCEL2", "ANNL2", "CASCADEHASHINGL2",
    // "FASTCASCADEHASHINGL2"}));
    // step->attributes()->addAttribute(att);

    // att = new Attribute();
    // att->setType(4); // boolean
    // att->setKey("useGuidedMatching");
    // att->setName("guided matching");
    // att->setTooltip(guidedMatchingTooltip);
    // att->setValue(false);
    // step->attributes()->addAttribute(att);
    // _steps->addStep(step);

    // sfm
    step = new Step("sfm");
    att = new Attribute();
    att->setType(3); // pair selector
    att->setKey("initial_pair");
    att->setName("initial pair");
    att->setTooltip(initialPairTooltip);
    att->setValue(QStringList({"", ""}));
    step->attributes()->addAttribute(att);

    // att = new Attribute();
    // att->setType(1); // slider
    // att->setKey("minTrackLength");
    // att->setName("min track length");
    // att->setTooltip(minimumTrackLengthTooltip);
    // att->setValue(3);
    // att->setMin(2);
    // att->setMax(40);
    // att->setStep(1);
    // step->attributes()->addAttribute(att);
    _steps->addStep(step);

    // meshing
    step = new Step("meshing");
    att = new Attribute();
    att->setType(4); // boolean
    att->setKey("enabled");
    att->setName("enabled");
    att->setTooltip(enableMeshingTooltip);
    step->attributes()->addAttribute(att);
    att->setValue(true);

    att = new Attribute();
    att->setType(1); // slider
    att->setKey("scale");
    att->setName("meshing scale");
    att->setTooltip(scaleTooltip);
    att->setValue(2);
    att->setMin(0);
    att->setMax(6);
    att->setStep(1);
    step->attributes()->addAttribute(att);
    _steps->addStep(step);

    // undistort
    step = new Step("undistort");
    att = new Attribute();
    att->setType(4); // boolean
    att->setKey("enabled");
    att->setName("enabled");
    att->setTooltip(undistortTooltip);
    step->attributes()->addAttribute(att);
    att->setValue(false);
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

void Job::deserializeFromJSON(const QJsonObject& obj)
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
