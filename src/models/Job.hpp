#pragma once

#include <QObject>
#include <QUrl>
#include <QDateTime>
#include <QProcess>
#include "StepModel.hpp"
#include "ResourceModel.hpp"

namespace meshroom
{

class Job : public QObject
{
    Q_OBJECT

public:
    Job(const QUrl& url = QUrl());

public:
    const QUrl& url() const { return _url; }
    const QString& name() const { return _name; }
    const QDateTime& date() const { return _date; }
    const QString& user() const { return _user; }
    const float& completion() const { return _completion; }
    const int& status() const { return _status; }
    const QUrl& thumbnail() const { return _thumbnail; }
    StepModel* steps() const { return _steps; }
    ResourceModel* images() const { return _images; }
    void setUrl(const QUrl& url);
    void setName(const QString& name);
    void setDate(const QDateTime& date);
    void setUser(const QString& user);
    void setCompletion(const float& completion);
    void setStatus(const int& status);
    void setThumbnail(const QUrl& thumbnail);
    void setModelIndex(const QModelIndex& id);

public slots:
    bool save();
    bool start();
    void refresh();
    void readProcessOutput(int exitCode, QProcess::ExitStatus s);
    void selectPair();
    void selectThumbnail();
    bool isPairA(const QUrl& url);
    bool isPairB(const QUrl& url);
    bool isPairValid();
    bool isValid();

signals:
    void dataChanged();

private:
    QUrl _url;
    QString _name;
    QDateTime _date;
    QString _user;
    float _completion = 0.f;
    int _status = -1;
    QUrl _thumbnail;
    StepModel* _steps;
    ResourceModel* _images;
    QPersistentModelIndex _modelIndex;
};

} // namespace
