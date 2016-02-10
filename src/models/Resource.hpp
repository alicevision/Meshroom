#pragma once

#include <QObject>
#include <QUrl>
#include <QString>

namespace meshroom
{

class Resource : public QObject
{
    Q_OBJECT
    Q_PROPERTY(QString name READ name CONSTANT)
    Q_PROPERTY(QUrl url READ url CONSTANT)
    Q_PROPERTY(bool exists READ exists CONSTANT)

public:
    Resource(const QUrl& url);
    Resource(const Resource& obj);

public slots:
    QString name() const { return _url.fileName(); }
    const QUrl& url() const { return _url; }
    const bool& exists() const { return _exists; }

public:
    void serializeToJSON(QJsonArray* array) const;

private:
    QUrl _url;
    bool _exists = true;
};

} // namespace
