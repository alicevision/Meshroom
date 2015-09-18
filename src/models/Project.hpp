#pragma once

#include <QObject>
#include <QUrl>
#include "JobModel.hpp"

namespace mockup
{

class Project : public QObject
{
    Q_OBJECT

public:
    Project(const QUrl& url);

public:
    QString name() const { return _url.fileName(); }
    const QUrl& url() const { return _url; }
    JobModel* jobs() const { return _jobs; }

private:
    QUrl _url;
    JobModel* _jobs;
};

} // namespace
