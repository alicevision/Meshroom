#pragma once

#include <QObject>
#include <QUrl>
#include <QVector3D>
#include <QMatrix4x4>

// FIXME: remove iostream
#include <iostream>

namespace mockup
{

class CameraModel : public QObject
{
    Q_OBJECT

    Q_PROPERTY(QString name READ name WRITE setName NOTIFY nameChanged)
    Q_PROPERTY(QUrl url READ url WRITE setUrl NOTIFY urlChanged)
    //Q_PROPERTY(QVector3D eye READ eye WRITE setEye NOTIFY eyeChanged)
    //Q_PROPERTY(QVector3D center READ center WRITE setCenter NOTIFY centerChanged)
    //Q_PROPERTY(QVector3D up READ up WRITE setUp NOTIFY upChanged)
    Q_PROPERTY(QMatrix4x4 viewMatrix READ viewMatrix WRITE setViewMatrix NOTIFY viewMatrixChanged)

public:
    CameraModel(const QUrl& url, QObject* parent);

public slots:
    QUrl url() const;
    void setUrl(const QUrl& url);
    QString name() const;
    void setName(const QString& name);
    //const QVector3D& eye() const;
    //void setEye(const QVector3D& eye);
    //const QVector3D& center() const;
    //void setCenter(const QVector3D& center);
    //const QVector3D& up() const;
    //void setUp(const QVector3D& up);
    const QMatrix4x4 & viewMatrix() const;
    void setViewMatrix(const QMatrix4x4 &mat); 


    void setLookAt(const QVector3D &lookAt){_lookAt=lookAt;}
    const QVector3D & lookAt() const {return _lookAt;}


signals:
    void urlChanged();
    void nameChanged();
    void eyeChanged();
    void centerChanged();
    void upChanged();
    void viewMatrixChanged();

private:
    QString _name;
    QUrl _url;
    QMatrix4x4  _viewMatrix;
    QVector3D   _lookAt;
};

} // namespace
