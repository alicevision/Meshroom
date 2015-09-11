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
    const QUrl& url() const { return _url; }
    const QString& date() const { return _date; }
    const QString& user() const { return _user; }
    const QString& note() const { return _note; }
    const QList<QObject*>& cameras() const { return _cameras; }
    const QList<QObject*>& resources() const { return _resources; }
    const QUrl& pairA() const { return _pairA; }
    const QUrl& pairB() const { return _pairB; }
    const int& describerPreset() const { return _describerPreset; }
    const int& meshingScale() const { return _meshingScale; }
    const float& completion() const { return _completion; }
    const int& status() const { return _status; }
    void setUrl(const QUrl& url);
    void setDate(const QString& date);
    void setUser(const QString& user);
    void setNote(const QString& note);
    void setResources(const QList<QObject*>& resources);
    void setPairA(const QUrl& url);
    void setPairB(const QUrl& url);
    void setDescriberPreset(const int& threshold);
    void setMeshingScale(const int& scale);
    void setCompletion(const float& completion);
    void setStatus(const int& status);
    void addResources(const QList<QUrl>& urls);
    void removeResources(const QList<QUrl>& urls);

public slots:
    QUrl buildUrl() const { return QUrl::fromLocalFile(_url.toLocalFile() + "/build"); }
    QUrl matchUrl() const { return QUrl::fromLocalFile(_url.toLocalFile() + "/build/matches"); }

public slots:
    bool save();
    void start();
    void stop();
    void refresh();
    void select();
    void remove();

public slots:
    void autoSaveON();
    void resolveInvalidInitialPair();
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
    QUrl _pairA;
    QUrl _pairB;
    int _describerPreset = 1; // HIGH
    int _meshingScale = 2;
    float _completion = 0.f;
    int _status = -1;
    QProcess _process;
};

} // namespace
