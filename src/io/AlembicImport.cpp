#if WITH_ALEMBIC

#include "AlembicImport.hpp"
#include <Alembic/AbcGeom/All.h>
#include <Alembic/AbcCoreFactory/All.h>
#include "gl/GLPointCloud.hpp"

using namespace Alembic::Abc;
namespace AbcG = Alembic::AbcGeom;
using namespace AbcG;

namespace mockup
{

// Top down insertion of 3d objects
void AlembicImport::visitObject(IObject iObj, GLScene& scene)
{
    const MetaData& md = iObj.getMetaData();
    if(IPoints::matches(md))
    {
        IPoints points(iObj, kWrapExisting);
        IPointsSchema ms = points.getSchema();
        P3fArraySamplePtr positions = ms.getValue().getPositions();
        // P3fArraySamplePtr _points;
        //_points = positions;
        auto pointCloud = new GLPointCloud();
        pointCloud->setRawData(positions->get(), positions->size());
        scene.append(pointCloud);
    }
    else if(ICamera::matches(md))
    {
    }

    // Recurse
    for(size_t i = 0; i < iObj.getNumChildren(); i++)
    {
        visitObject(iObj.getChild(i), scene);
    }
}

AlembicImport::AlembicImport(const char* filename)
{
    Alembic::AbcCoreFactory::IFactory factory;
    Alembic::AbcCoreFactory::IFactory::CoreType coreType;
    Abc::IArchive archive = factory.getArchive(filename, coreType);

    // TODO : test if archive is correctly opened
    _rootEntity = archive.getTop();
}

void AlembicImport::populate(GLScene& scene)
{
    // TODO : handle the case where the archive wasn't correctly opened
    visitObject(_rootEntity, scene);
}

// const void* AlembicImport::pointCloudData()
//{
//    if(_points)
//    {
//        return _points->get();
//    }
//    std::cout << "no points in file" << std::endl;
//    return nullptr;
//}
//
// size_t AlembicImport::pointCloudSize()
//{
//    return _points->size();
//}

} // namespace

#endif // WITH_ALEMBIC
