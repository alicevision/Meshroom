#pragma once

#include <QObject>
#include <QUrl>
#include <QProcess>

namespace mockup
{

class CameraModel; // forward declaration

class JobModel : public QObject
{
    Q_OBJECT
    Q_PROPERTY(QUrl url READ url WRITE setUrl NOTIFY urlChanged)
    Q_PROPERTY(QString date READ date NOTIFY dateChanged)
    Q_PROPERTY(QString user READ user NOTIFY userChanged)
    Q_PROPERTY(QString note READ note WRITE setNote NOTIFY noteChanged)
    Q_PROPERTY(QList<QObject*> resources READ resources WRITE setResources NOTIFY resourcesChanged)
    Q_PROPERTY(QList<QObject*> cameras READ cameras NOTIFY camerasChanged)
    Q_PROPERTY(QList<QString> steps READ steps WRITE setSteps NOTIFY stepsChanged)
    Q_PROPERTY(QUrl pairA READ pairA WRITE setPairA NOTIFY pairAChanged)
    Q_PROPERTY(QUrl pairB READ pairB WRITE setPairB NOTIFY pairBChanged)
    Q_PROPERTY(int describerPreset READ describerPreset WRITE setDescriberPreset NOTIFY
                   describerPresetChanged)
    Q_PROPERTY(int meshingScale READ meshingScale WRITE setMeshingScale NOTIFY meshingScaleChanged)
    Q_PROPERTY(float completion READ completion NOTIFY completionChanged)
    Q_PROPERTY(int status READ status NOTIFY statusChanged)

public:
    JobModel(QObject* parent = nullptr);
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
    const QList<QObject*>& resources() const;
    void setResources(const QList<QObject*>& resources);
    void addResources(const QList<QUrl>& urls);
    void removeResources(const QList<QUrl>& urls);
    const QList<QString>& steps() const;
    void setSteps(const QList<QString>& steps);
    const QUrl& pairA() const;
    void setPairA(const QUrl& url);
    const QUrl& pairB() const;
    void setPairB(const QUrl& url);
    const int& describerPreset() const;
    void setDescriberPreset(const int& threshold);
    const int& meshingScale() const;
    void setMeshingScale(const int& scale);
    const float& completion() const;
    void setCompletion(const float& completion);
    const int& status() const;
    void setStatus(const int& status);

public slots:
    QUrl buildUrl() const;
    QUrl matchUrl() const;
    void autoSaveON();
    bool save();
    void start();
    void stop();
    void refresh();
    void select();
    void remove();

public slots:
    void readProcessOutput(int exitCode, QProcess::ExitStatus exitStatus);

public:
    static QString describerPresetString(const int& describerPreset);
    static int describerPresetId(const QString& describerPreset);

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
    void pairAChanged();
    void pairBChanged();
    void describerPresetChanged();
    void meshingScaleChanged();
    void completionChanged();
    void statusChanged();

private:
    QUrl _url;
    QString _date;
    QString _user;
    QString _note;
    QList<QObject*> _cameras;
    QList<QObject*> _resources;
    QList<QString> _steps;
    QUrl _pairA;
    QUrl _pairB;
    int _describerPreset = 1; // HIGH
    int _meshingScale = 2;
    float _completion = 0.f;
    int _status = -1;
    QProcess _process;
};

} // namespace
