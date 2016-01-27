#pragma once

#include <QObject>
#include <QUrl>
#include <QString>

namespace meshroom
{

class Resource : public QObject
{
    Q_OBJECT

public:
    Resource(const QUrl& url);
    Resource(const Resource& obj);

public:
    QString name() const { return _url.fileName(); }
    const QUrl& url() const { return _url; }

public:
    void serializeToJSON(QJsonArray* array) const;

private:
    QUrl _url;
};

} // namespace
