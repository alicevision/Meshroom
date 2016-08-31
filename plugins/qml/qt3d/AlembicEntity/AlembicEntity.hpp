#pragma once

#include <QEntity>
#include <QUrl>
#include <Alembic/AbcGeom/All.h>
#include <Alembic/AbcCoreFactory/All.h>
#include <Qt3DRender/QParameter>
#include <Qt3DRender/QMaterial>
#include <Qt3DRender/QCamera>
#include <Qt3DExtras/QPerVertexColorMaterial>

namespace abcentity
{

class AlembicEntity : public Qt3DCore::QEntity
{
    Q_OBJECT
    Q_PROPERTY(QUrl url READ url WRITE setUrl NOTIFY urlChanged)
    Q_PROPERTY(float particleSize READ particleSize WRITE setParticleSize NOTIFY particleSizeChanged)

public:
    AlembicEntity(Qt3DCore::QNode* = nullptr);
    ~AlembicEntity() = default;

public:
    Q_SLOT const QUrl& url() const { return _url; }
    Q_SLOT const float& particleSize() const { return _particleSize; }
    Q_SLOT void setUrl(const QUrl&);
    Q_SLOT void setParticleSize(const float&);

private:
    void loadAbcArchive();
    void visitAbcObject(Alembic::Abc::IObject, Alembic::Abc::M44d, Qt3DCore::QEntity*);
    void createMaterials();

public:
    Q_SIGNAL void urlChanged();
    Q_SIGNAL void particleSizeChanged();

private:
    QUrl _url;
    float _particleSize = 0.5;
    Qt3DRender::QParameter* _particleSizeParameter;
    Qt3DRender::QMaterial* _pointCloudMaterial;
    Qt3DExtras::QPerVertexColorMaterial* _cameraMaterial;
};

} // namespace
