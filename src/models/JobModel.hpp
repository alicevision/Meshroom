#pragma once

#include "io/JobsIO.hpp"
#include <QObject>
#include <QUrl>

namespace mockup
{

class CameraModel; // forward declaration

class JobModel : public QObject
{
    Q_OBJECT
    Q_PROPERTY(QUrl url READ url WRITE setUrl NOTIFY urlChanged)
    Q_PROPERTY(QString date READ date WRITE setDate NOTIFY dateChanged)
    Q_PROPERTY(QString user READ user WRITE setUser NOTIFY userChanged)
    Q_PROPERTY(QString note READ note WRITE setNote NOTIFY noteChanged)
    Q_PROPERTY(QList<QObject*> resources READ resources WRITE setResources NOTIFY resourcesChanged)
    Q_PROPERTY(QList<QObject*> cameras READ cameras WRITE setCameras NOTIFY camerasChanged)
    Q_PROPERTY(QList<QString> steps READ steps WRITE setSteps NOTIFY stepsChanged)
    Q_PROPERTY(QList<QUrl> pair READ pair WRITE setPair NOTIFY pairChanged)
    Q_PROPERTY(float peakThreshold READ peakThreshold WRITE setPeakThreshold NOTIFY
                   peakThresholdChanged)
    Q_PROPERTY(int meshingScale READ meshingScale WRITE setMeshingScale NOTIFY meshingScaleChanged)
    Q_PROPERTY(float completion READ completion WRITE setCompletion NOTIFY completionChanged)
    Q_PROPERTY(bool running READ running WRITE setRunning NOTIFY runningChanged)

public:
    enum ERROR_TYPE
    {
        ERR_NOERROR = 0,
        ERR_INVALID_URL,
        ERR_INVALID_DESCRIPTOR,
        ERR_MALFORMED_DESCRIPTOR,
        ERR_SOURCE_LACK,
        ERR_INVALID_INITIAL_PAIR
    };

public:
    JobModel(const QUrl& url, QObject* parent);
    ~JobModel() = default;

public slots:
    const QUrl& url() const;
    void setUrl(const QUrl& url);
    const QString& date() const;
    void setDate(const QString& date);
    const QString& user() const;
    void setUser(const QString& user);
    const QString& note() const;
    void setNote(const QString& note);
    const QList<QObject*>& cameras() const;
    void setCameras(const QList<QObject*>& name);
    const QList<QObject*>& resources() const;
    void setResources(const QList<QObject*>& resources);
    void addResources(const QList<QUrl>& urls);
    void removeResources(const QList<QUrl>& urls);
    const QList<QString>& steps() const;
    void setSteps(const QList<QString>& steps);
    const QList<QUrl>& pair() const;
    void setPair(const QList<QUrl>& pair);
    bool addPairElement(const QUrl& url);
    bool removePairElement(const QUrl& url);
    const float& peakThreshold() const;
    void setPeakThreshold(const float& threshold);
    const int& meshingScale() const;
    void setMeshingScale(const int& scale);
    const float& completion() const;
    void setCompletion(const float& completion);
    const bool& running() const;
    void setRunning(const bool& running);
    QUrl buildUrl() const;
    QUrl matchUrl() const;

public slots:
    ERROR_TYPE error() const;
    QString errorString() const;
    void setError(ERROR_TYPE e);

public slots:
    void start();
    void stop();
    void refresh();

public slots:
    bool loadFromDisk();
    bool saveToDisk() const;

private:
    void setCamerasFromResources();

signals:
    void urlChanged();
    void dateChanged();
    void userChanged();
    void noteChanged();
    void camerasChanged();
    void resourcesChanged();
    void stepsChanged();
    void pairChanged();
    void peakThresholdChanged();
    void meshingScaleChanged();
    void completionChanged();
    void runningChanged();

private:
    QUrl _url;
    QString _date;
    QString _user;
    QString _note;
    QList<QObject*> _cameras;
    QList<QObject*> _resources;
    QList<QString> _steps;
    QList<QUrl> _pair;
    float _peakThreshold = 0.04f;
    int _meshingScale = 1;
    float _completion = 0.f;
    bool _running = true;
    ERROR_TYPE _error = ERR_NOERROR;
    JobsIO _io;
};

} // namespace
