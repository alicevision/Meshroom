#pragma once

#include <QObject>
#include <QStringList>
#include <QUrl>

namespace mockup
{

class ResourceModel : public QObject
{
    Q_OBJECT
    Q_PROPERTY(QUrl url READ url WRITE setUrl NOTIFY urlChanged)
    Q_PROPERTY(QString name READ name WRITE setName NOTIFY nameChanged)

public:
    ResourceModel(const QUrl& url, QObject* parent);

public slots:
    QUrl url() const;
    void setUrl(const QUrl& url);
    const QString& name() const;
    void setName(const QString& name);
    bool isDir() const;

public:
    static bool isValidUrl(const QUrl& url);
    static QStringList validFileExtensions()
    {
        QStringList extensions;
        extensions << "*.jpg"
                   << "*.jpeg";
        return extensions;
    }

signals:
    void urlChanged();
    void nameChanged();

private:
    QUrl _url;
    QString _name;
    bool _isDir = false;
};

} // namespace
