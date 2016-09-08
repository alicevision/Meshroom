#pragma once

#include <QEntity>
#include <QUrl>
#include <Alembic/AbcGeom/All.h>
#include <Alembic/AbcCoreFactory/All.h>
#include <Qt3DRender/QParameter>
#include <Qt3DRender/QMaterial>

namespace abcentity
{

class AlembicEntity : public Qt3DCore::QEntity
{
    Q_OBJECT
    Q_PROPERTY(QUrl url READ url WRITE setUrl NOTIFY urlChanged)
    Q_PROPERTY(float particleSize READ particleSize WRITE setParticleSize NOTIFY particleSizeChanged)
    Q_PROPERTY(float locatorScale READ locatorScale WRITE setLocatorScale NOTIFY locatorScaleChanged)

public:
    AlembicEntity(Qt3DCore::QNode* = nullptr);
    ~AlembicEntity() = default;

public:
    Q_SLOT const QUrl& url() const { return _url; }
    Q_SLOT const float& particleSize() const { return _particleSize; }
    Q_SLOT const float& locatorScale() const { return _locatorScale; }
    Q_SLOT void setUrl(const QUrl&);
    Q_SLOT void setParticleSize(const float&);
    Q_SLOT void setLocatorScale(const float&);

private:
    void createMaterials();
    void loadAbcArchive();
    void visitAbcObject(Alembic::Abc::IObject, Alembic::Abc::M44d);

public:
    Q_SIGNAL void urlChanged();
    Q_SIGNAL void particleSizeChanged();
    Q_SIGNAL void locatorScaleChanged();

private:
    QUrl _url;
    float _particleSize = 0.5;
    float _locatorScale = 1.0;
    Qt3DRender::QParameter* _particleSizeParameter;
    Qt3DRender::QMaterial* _cloudMaterial;
    Qt3DRender::QMaterial* _cameraMaterial;
};

} // namespace
