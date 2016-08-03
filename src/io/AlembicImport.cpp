#if WITH_ALEMBIC

#include "AlembicImport.hpp"
#include <Alembic/AbcGeom/All.h>
#include <Alembic/AbcCoreFactory/All.h>
#include "gl/GLPointCloud.hpp"
#include "gl/GLCamera.hpp"

using namespace Alembic::Abc;
namespace AbcG = Alembic::AbcGeom;
using namespace AbcG;

namespace meshroom
{

template<class ABCSCHEMA>
inline ICompoundProperty getAbcUserProperties(ABCSCHEMA& schema)
{
  ICompoundProperty userProps = schema.getUserProperties();
  if(userProps && userProps.getNumProperties() != 0)
    return userProps;

  // Maya always use ArbGeomParams instead of user properties.
  return schema.getArbGeomParams();
}

// Top down insertion of 3d objects
void AlembicImport::visitObject(IObject iObj, GLScene& scene, M44d mat)
{
    const MetaData& md = iObj.getMetaData();
    if(IPoints::matches(md))
    {
        IPoints points(iObj, kWrapExisting);
        IPointsSchema ms = points.getSchema();
        P3fArraySamplePtr positions = ms.getValue().getPositions();
        auto pointCloud = new GLPointCloud();
        pointCloud->setRawPositions(positions->get(), positions->size());

        // Check if we have a color property
        bool colored = false;
        ICompoundProperty arbProp = ms.getArbGeomParams();
        if(arbProp)
        {
            std::size_t numProps = arbProp.getNumProperties();
            for(std::size_t i = 0; i < numProps; ++i)
            {
                const PropertyHeader& propHeader = arbProp.getPropertyHeader(i);
                if(propHeader.isArray())
                {
                    const std::string& propName = propHeader.getName();
                    Alembic::Abc::IArrayProperty prop(arbProp, propName);

                    Alembic::AbcCoreAbstract::DataType dtype = prop.getDataType();
                    std::string interp = prop.getMetaData().get("interpretation");

                    if(interp == "rgb")
                    {
                        Alembic::Util::uint8_t extent = dtype.getExtent();
                        std::cout << "Loading " << propName << " " << interp << " " << extent
                                  << std::endl;

                        Alembic::AbcCoreAbstract::ArraySamplePtr samp;
                        prop.get(samp);

                        pointCloud->setRawColors(samp->getData(), samp->size());
                        colored = true;
                        break; // set colors only once
                    }
                }
            }
        }
        if(!colored)
        {
            float* defaultColor = new float[positions->size() * 3];
            for(int i = 0; i < positions->size() * 3; i++)
                defaultColor[i] = 1.f;
            pointCloud->setRawColors(defaultColor, positions->size());
            delete[] defaultColor;
        }
        // get the visibility
        ICompoundProperty userProps = getAbcUserProperties(ms);
        if(userProps && userProps.getPropertyHeader("mvg_visibilitySize") &&
                userProps.getPropertyHeader("mvg_visibilityIds"))
        {
            IUInt32ArrayProperty propVisibilitySize(userProps, "mvg_visibilitySize");
            UInt32ArraySamplePtr sampleVisibilitySize;
            propVisibilitySize.get(sampleVisibilitySize);

            if(positions->size() != sampleVisibilitySize->size())
            {
                std::cerr << "ABC Error: number of observations per 3D point should be identical to the number of 2D features." << std::endl;
                std::cerr << "Number of observations per 3D point size is " << sampleVisibilitySize->size() << std::endl;
                std::cerr << "Number of 3D points is " << positions->size() << std::endl;
                throw std::runtime_error("Failed loading the alembic file, visibility size is not the same as the number of points.");
            }
            std::vector<std::size_t> vec_visibility(sampleVisibilitySize->size(), 0);
            for(std::size_t point3d_i = 0; point3d_i < positions->size(); ++point3d_i)
            {
                vec_visibility[point3d_i] = (*sampleVisibilitySize)[point3d_i];
            }
            
            assert(vec_visibility.size() == sampleVisibilitySize->size());
            
            pointCloud->setRawVisibility(vec_visibility, vec_visibility.size());
        }
        scene.append(pointCloud);
    }
    else if(IXform::matches(md))
    {
        IXform xform(iObj, kWrapExisting);
        XformSample xs;
        xform.getSchema().get(xs);
        mat *= xs.getMatrix();
    }
    else if(ICamera::matches(md))
    {
        ICamera camera(iObj, kWrapExisting);
        ICameraSchema cs = camera.getSchema();

        auto newCamera = new GLCamera();
        QMatrix4x4 modelMat(mat[0][0], mat[1][0], mat[2][0], mat[3][0], mat[0][1], mat[1][1],
                            mat[2][1], mat[3][1], mat[0][2], mat[1][2], mat[2][2], mat[3][2],
                            mat[0][3], mat[1][3], mat[2][3], mat[3][3]);
        newCamera->setModelMatrix(modelMat);
        CameraSample matrix = cs.getValue();
        QMatrix4x4 projMat;
        newCamera->setProjectionMatrix(projMat);

        // Check if we have an associated image plane
        ICompoundProperty userProps = cs.getUserProperties();
        if(userProps)
        {
            std::size_t numProps = userProps.getNumProperties();
            for(std::size_t i = 0; i < numProps; ++i)
            {
                const PropertyHeader& propHeader = userProps.getPropertyHeader(i);
                if(propHeader.getName() == "imagePlane")
                {
                    Alembic::Abc::IStringProperty prop(userProps, "imagePlane");
                    std::string imagePlaneFile;
                    prop.get(imagePlaneFile);
                    newCamera->setImagePlane(imagePlaneFile);
                    break;
                }
            }
        }
        scene.append(newCamera);
    }

    // Recurse
    for(size_t i = 0; i < iObj.getNumChildren(); i++)
    {
        visitObject(iObj.getChild(i), scene, mat);
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
    M44d xformMat;
    visitObject(_rootEntity, scene, xformMat);
}
}
#endif // WITH_ALEMBIC
