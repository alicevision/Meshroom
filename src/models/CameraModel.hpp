#pragma once

#include <QObject>
#include <QUrl>

namespace mockup
{

class CameraModel : public QObject
{
    Q_OBJECT

    Q_PROPERTY(QString name READ name WRITE setName NOTIFY nameChanged)
    Q_PROPERTY(QUrl url READ url WRITE setUrl NOTIFY urlChanged)

public:
    CameraModel(const QUrl& url, QObject* parent);

public slots:
    QUrl url() const;
    void setUrl(const QUrl& url);
    QString name() const;
    void setName(const QString& name);

signals:
    void urlChanged();
    void nameChanged();

private:
    QString _name;
    QUrl _url;
};

} // namespace
