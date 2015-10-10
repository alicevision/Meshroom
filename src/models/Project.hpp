#pragma once

#include <QObject>
#include <QUrl>
#include <QSortFilterProxyModel>
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
    QSortFilterProxyModel* proxy() const { return _proxy; }

public slots:
    void setFilterRegexp(const QString& regexp) {
        _proxy->setFilterRegExp(QRegExp(regexp));
    }

private:
    QUrl _url;
    JobModel* _jobs;
    QSortFilterProxyModel* _proxy;
};

} // namespace
