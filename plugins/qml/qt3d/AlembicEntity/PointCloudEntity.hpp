#pragma once

#include <QEntity>
#include <Alembic/AbcGeom/All.h>
#include <Alembic/AbcCoreFactory/All.h>

namespace abcentity
{

class PointCloudEntity : public Qt3DCore::QEntity
{
    Q_OBJECT

public:
    PointCloudEntity(Qt3DCore::QNode* = nullptr);
    ~PointCloudEntity() = default;

public:
    void setData(const Alembic::Abc::IObject&);
    void setTransform(const Alembic::Abc::M44d&);
};

} // namespace
