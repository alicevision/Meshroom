#pragma once

#include <QObject>
#include <QUrl>
#include <QString>

namespace meshroom
{

class Template : public QObject
{
    Q_OBJECT
    Q_PROPERTY(QString name READ name CONSTANT)
    Q_PROPERTY(QUrl url READ url CONSTANT)
    Q_PROPERTY(QString description READ description CONSTANT)

public:
    Template(QObject*, const QUrl&);

public:
    Q_SLOT QString name() const { return _name; }
    Q_SLOT QUrl url() const { return _url; }
    Q_SLOT QString description() const { return _description; }

private:
    QString _name;
    QUrl _url;
    QString _description;
};

} // namespace
