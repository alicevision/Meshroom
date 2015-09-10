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
    Q_PROPERTY(bool isPairImageA READ isPairImageA NOTIFY isPairImageAChanged)
    Q_PROPERTY(bool isPairImageB READ isPairImageB NOTIFY isPairImageBChanged)

public:
    ResourceModel(const QUrl& url, QObject* parent);

public slots:
    const QUrl& url() const { return _url; }
    const QString& name() const { return _name; }
    bool isPairImageA() const { return _isPairImageA; }
    bool isPairImageB() const { return _isPairImageB; }
    void setUrl(const QUrl& url);
    void setName(const QString& name);
    void setIsPairImageA(const bool b);
    void setIsPairImageB(const bool b);

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
    void isPairImageAChanged();
    void isPairImageBChanged();

private:
    QUrl _url;
    QString _name;
    bool _isPairImageA = false;
    bool _isPairImageB = false;
};

} // namespace
