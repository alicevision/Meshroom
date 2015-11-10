#pragma once

#include <QObject>
#include <QUrl>
#include <QSortFilterProxyModel>
#include "JobModel.hpp"

namespace meshroom
{

class Project : public QObject
{
    Q_OBJECT

public:
    Project(const QUrl& url);

public:
    const QUrl& url() const { return _url; }
    QString name() const { return _name; }
    JobModel* jobs() const { return _jobs; }
    QSortFilterProxyModel* proxy() const { return _proxy; }
    void setName(const QString& name);

public slots:
    bool load();
    bool save();
    void setFilterRegexp(const QString& regexp);

private:
    void populate();
    void serializeToJSON(QJsonObject* obj) const;
    void deserializeFromJSON(const QJsonObject& obj);

signals:
    void dataChanged();

private:
    QUrl _url;
    QString _name;
    JobModel* _jobs;
    QSortFilterProxyModel* _proxy;
};

} // namespace
