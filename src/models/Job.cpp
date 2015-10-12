#include "Job.hpp"
#include "JobModel.hpp"
#include "io/JobsIO.hpp"
#include <QCoreApplication>
#include <QJsonDocument>
#include <QJsonObject>
#include <QFileInfo>
#include <QDebug>
#include <cstdlib> // std::getenv
#include <cassert>

namespace mockup
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
        return nullptr;
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
    {
        Step* step = new Step("feature_detection");
        Attribute* att = new Attribute();
        att->setType(2); // combo
        att->setKey("describerPreset");
        att->setName("quality");
        att->setValue("Normal");
        att->setOptions(QStringList({"Normal", "High", "Ultra"}));
        step->attributes()->addAttribute(att);
        _steps->addStep(step);
    }

    {
        Step* step = new Step("meshing");
        Attribute* att = new Attribute();
        att->setType(1); // slider
        att->setKey("scale");
        att->setName("meshing scale");
        att->setValue(2);
        att->setMin(1);
        att->setMax(10);
        att->setStep(1);
        step->attributes()->addAttribute(att);
        _steps->addStep(step);
    }

    {
        Step* step = new Step("sfm");
        {
            Attribute* att = new Attribute();
            att->setType(3); // pair selector
            att->setKey("initial_pair");
            att->setName("initial pair");
            att->setValue(QStringList({"", ""}));
            step->attributes()->addAttribute(att);
        }
        _steps->addStep(step);
    }

    JobsIO::load(*this);

    // initial_pair automatic selection
    QObject::connect(_images, SIGNAL(countChanged(int)), this, SLOT(selectPair()));

    // thumbnail selection
    QObject::connect(_images, SIGNAL(countChanged(int)), this, SLOT(selectThumbnail()));

    // job auto-save
    connect(_images, SIGNAL(countChanged(int)), this, SLOT(save()));
    for(size_t i = 0; i < _steps->rowCount(); i++)
    {
        QModelIndex id = _steps->index(i, 0);
        Step* step = _steps->data(id, StepModel::ModelDataRole).value<Step*>();
        connect(step->attributes(), SIGNAL(dataChanged(const QModelIndex&, const QModelIndex&)),
                this, SLOT(save()));
    }
}

bool Job::save()
{
    return JobsIO::save(*this);
}

void Job::start()
{
    JobModel* model = qobject_cast<JobModel*>(parent());
    assert(model);

    if(_images->rowCount() < 2)
    {
        qCritical("Starting job: insufficient number of sources");
        return;
    }

    if(!isPairValid())
    {
        qCritical("Starting job: invalid initial pair");
        return;
    }

    // define program path
    QString startCommand = std::getenv("MOCKUP_START_COMMAND");
    if(startCommand.isEmpty())
        startCommand = QCoreApplication::applicationDirPath() + "/scripts/job_start.py";

    // and command arguments
    QStringList arguments;
    arguments.append(_url.toLocalFile() + "/job.json");

    // configure & run
    QProcess process;
    process.setProgram(startCommand);
    process.setArguments(arguments);
    process.start();
    if(!process.waitForFinished())
    {
        qCritical("Unable to start job");
        return;
    }

    model->setData(_modelIndex, 0, JobModel::StatusRole); // BLOCKED
    qInfo("Job started");
}

void Job::refresh()
{
    QFileInfo fileInfo(_url.toLocalFile() + "/job.json");
    if(!fileInfo.exists())
        return;

    // define program path
    QString statusCommand = std::getenv("MOCKUP_STATUS_COMMAND");
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
        qCritical("Unable to refresh job");
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
        qCritical("Invalid JSON response: parse error");
        model->setData(_modelIndex, 4, JobModel::StatusRole); // ERROR
        return;
    }

    // retrieve & set job completion & status
    QJsonObject json = jsondoc.object();
    if(!json.contains("completion") || !json.contains("status"))
    {
        qCritical("Invalid response: missing values");
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

} // namespace
