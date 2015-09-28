#pragma once

#if WITH_ALEMBIC

#include <Alembic/AbcGeom/All.h>
#include <Alembic/AbcCoreHDF5/All.h>
#include "gl/GLScene.hpp"

using namespace Alembic::Abc;
namespace AbcG = Alembic::AbcGeom;
using namespace AbcG;

namespace mockup
{

class AlembicImport // FIXME rename Import->Importer
{
public:
    explicit AlembicImport(const char* fileName);
    ~AlembicImport() = default;

    void populate(GLScene&);

private:
    void visitObject(IObject, GLScene&, M44d);
    IObject _rootEntity;
};

} // namespace mockup

#endif // WITH_ALEMBIC
