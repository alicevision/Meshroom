#pragma once

#include <QObject>
#include <QUrl>
#include <QVector3D>
#include <QMatrix4x4>

namespace mockup
{

class CameraModel : public QObject
{
    Q_OBJECT

    Q_PROPERTY(QString name READ name WRITE setName NOTIFY nameChanged)
    Q_PROPERTY(QUrl url READ url WRITE setUrl NOTIFY urlChanged)
    Q_PROPERTY(QVector3D eye READ eye WRITE setEye NOTIFY eyeChanged)
    Q_PROPERTY(QVector3D center READ center WRITE setCenter NOTIFY centerChanged)
    Q_PROPERTY(QVector3D up READ up WRITE setUp NOTIFY upChanged)

public:
    CameraModel(const QUrl& url, QObject* parent);

public slots:
    QUrl url() const;
    void setUrl(const QUrl& url);
    QString name() const;
    void setName(const QString& name);
    const QVector3D& eye() const;
    void setEye(const QVector3D& eye);
    const QVector3D& center() const;
    void setCenter(const QVector3D& center);
    const QVector3D& up() const;
    void setUp(const QVector3D& up);

public:
    QMatrix4x4 viewMatrix() const;

signals:
    void urlChanged();
    void nameChanged();
    void eyeChanged();
    void centerChanged();
    void upChanged();

private:
    QString _name;
    QUrl _url;
    QVector3D _eye = QVector3D(4, 3, 4);
    QVector3D _center = QVector3D(0, 0, 0);
    QVector3D _up = QVector3D(0, 1, 0);
};

} // namespace
