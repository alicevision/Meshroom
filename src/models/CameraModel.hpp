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
    Q_PROPERTY(QMatrix4x4 viewMatrix READ viewMatrix WRITE setViewMatrix NOTIFY viewMatrixChanged)

public:
    CameraModel(const QUrl& url, QObject* parent);

public slots:
    QUrl url() const;
    void setUrl(const QUrl& url);
    QString name() const;
    void setName(const QString& name);
    const QMatrix4x4& viewMatrix() const;
    void setViewMatrix(const QMatrix4x4& mat);
    void setLookAtRadius(float radius) { _lookAtRadius = radius > 0.0 ? radius : 0.0; }
    float lookAtRadius() { return _lookAtRadius; }
    QVector3D lookAt() const;

signals:
    void urlChanged();
    void nameChanged();
    void viewMatrixChanged();

private:
    QString _name;
    QUrl _url;
    QMatrix4x4 _viewMatrix; // TODO : add projection matrix
    float _lookAtRadius;
};

} // namespace
