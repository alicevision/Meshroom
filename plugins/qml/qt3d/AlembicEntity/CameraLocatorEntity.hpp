#pragma once

#include <QEntity>
#include <Alembic/AbcGeom/All.h>
#include <Alembic/AbcCoreFactory/All.h>

namespace abcentity
{

class CameraLocatorEntity : public Qt3DCore::QEntity
{
    Q_OBJECT

public:
    CameraLocatorEntity(Qt3DCore::QNode* = nullptr);
    ~CameraLocatorEntity() = default;

public:
    void setTransform(const Alembic::Abc::M44d&);
};

} // namespace
