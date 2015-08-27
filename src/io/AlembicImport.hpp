#pragma once

#if WITH_ALEMBIC
#include <Alembic/AbcGeom/All.h>
#include <Alembic/AbcCoreHDF5/All.h>

using namespace Alembic::Abc;
namespace AbcG = Alembic::AbcGeom;
using namespace AbcG;

namespace mockup 
{

class AlembicImport // FIXME rename Import->Importer
{
public:
    explicit AlembicImport(const char *fileName);
    ~AlembicImport() = default;

    // void populateScene();
    //void populateRenderer(Renderer &r)
    const void* pointCloudData();
    size_t pointCloudSize();
    void visitObject( IObject );
private:
    P3fArraySamplePtr _points;
};

} // namespace mockup
#endif // WITH_ALEMBIC
