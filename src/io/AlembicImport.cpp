#if WITH_ALEMBIC

#include "AlembicImport.hpp"
#include <Alembic/AbcGeom/All.h>
#include <Alembic/AbcCoreFactory/All.h>

using namespace Alembic::Abc;
namespace AbcG = Alembic::AbcGeom;
using namespace AbcG;

namespace mockup
{

void AlembicImport::visitObject(IObject iObj)
{
    const MetaData& md = iObj.getMetaData();
    if(IPoints::matches(md))
    {
        IPoints points(iObj, kWrapExisting);
        IPointsSchema ms = points.getSchema();
        P3fArraySamplePtr positions = ms.getValue().getPositions();
        _points = positions;
        return;
    }

    // Recurse
    for(size_t i = 0; i < iObj.getNumChildren(); i++)
    {
        visitObject(iObj.getChild(i));
    }
}

AlembicImport::AlembicImport(const char* filename)
{
    Alembic::AbcCoreFactory::IFactory factory;
    Alembic::AbcCoreFactory::IFactory::CoreType coreType;
    Abc::IArchive archive = factory.getArchive(filename, coreType);

    auto rootEntity = archive.getTop();
    visitObject(rootEntity);
    std::cout << "imported alembic" << std::endl;
}

const void* AlembicImport::pointCloudData()
{
    if(_points)
    {
        return _points->get();
    }
    std::cout << "no points in file" << std::endl;
    return nullptr;
}

size_t AlembicImport::pointCloudSize()
{
    return _points->size();
}
}
#endif // WITH_ALEMBIC
