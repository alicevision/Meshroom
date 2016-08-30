#include "AlembicEntity.hpp"
#include <Qt3DCore/QTransform>
#include <Qt3DRender/QGeometryRenderer>
#include <Qt3DRender/QAttribute>
#include <Qt3DRender/QBuffer>
#include <Qt3DRender/QEffect>
#include <Qt3DRender/QTechnique>
#include <Qt3DRender/QRenderPass>
#include <Qt3DRender/QShaderProgram>
#include <QVector3D>
#include <QDebug>

namespace abcentity
{

AlembicEntity::AlembicEntity(Qt3DCore::QNode* parent)
    : Qt3DCore::QEntity(parent)
    , _particleSizeParameter(new Qt3DRender::QParameter)
{
    createMaterials();
}

void AlembicEntity::setUrl(const QUrl& value)
{
    if(_url == value)
        return;
    _url = value;
    loadAbcArchive();
    Q_EMIT urlChanged();
}

void AlembicEntity::setParticleSize(const float& value)
{
    if(_particleSize == value)
        return;
    _particleSize = value;
    _particleSizeParameter->setValue(value);
    Q_EMIT particleSizeChanged();
}

// private
void AlembicEntity::loadAbcArchive()
{
    if(!_url.isValid())
        return;

    using namespace Alembic::Abc;
    using namespace Alembic::AbcGeom;

    // clear entity (remove direct children & all components)
    QList<QEntity*> entities = findChildren<QEntity*>("", Qt::FindDirectChildrenOnly);
    for(auto entity : entities)
        delete entity;
    for(auto& component : components())
        removeComponent(component);

    // load the abc archive
    Alembic::AbcCoreFactory::IFactory factory;
    Alembic::AbcCoreFactory::IFactory::CoreType coreType;
    Abc::IArchive archive = factory.getArchive(_url.toLocalFile().toStdString(), coreType);
    if(!archive.valid())
        return;

    // visit the abc tree
    M44d xformMat;
    visitAbcObject(archive.getTop(), xformMat, this);
}

// private
void AlembicEntity::visitAbcObject(Alembic::Abc::IObject iObj, Alembic::Abc::M44d mat, Qt3DCore::QEntity* entity)
{
    using namespace Qt3DRender;
    using namespace Alembic::Abc;
    using namespace Alembic::AbcGeom;

    const MetaData& md = iObj.getMetaData();
    if(IPoints::matches(md))
    {
        // create a new geometry renderer
        QGeometryRenderer *customMeshRenderer = new QGeometryRenderer;
        QGeometry* customGeometry = new QGeometry;

        // read position data
        IPoints points(iObj, kWrapExisting);
        IPointsSchema schema = points.getSchema();
        P3fArraySamplePtr positions = schema.getValue().getPositions();
        size_t npoints = positions->size();

        // vertices buffer
        QByteArray positionData((const char *)positions->get(), npoints * 3 * sizeof(float));
        QBuffer* vertexDataBuffer = new QBuffer(QBuffer::VertexBuffer);
        vertexDataBuffer->setData(positionData);
        QAttribute *positionAttribute = new QAttribute;
        positionAttribute->setAttributeType(QAttribute::VertexAttribute);
        positionAttribute->setBuffer(vertexDataBuffer);
        positionAttribute->setDataType(QAttribute::Float);
        positionAttribute->setDataSize(3);
        positionAttribute->setByteOffset(0);
        positionAttribute->setByteStride(3 * sizeof(float));
        positionAttribute->setCount(npoints);
        positionAttribute->setName(QAttribute::defaultPositionAttributeName());
        customGeometry->addAttribute(positionAttribute);
        customGeometry->setBoundingVolumePositionAttribute(positionAttribute);

        // read color data
        QBuffer* colorDataBuffer = new QBuffer(QBuffer::VertexBuffer);

        // check if we have a color property
        ICompoundProperty cProp = schema.getArbGeomParams();
        if(cProp)
        {
            std::size_t numProps = cProp.getNumProperties();
            for(std::size_t i = 0; i < numProps; ++i)
            {
                const PropertyHeader& propHeader = cProp.getPropertyHeader(i);
                if(propHeader.isArray())
                {
                    const std::string& propName = propHeader.getName();
                    Alembic::Abc::IArrayProperty prop(cProp, propName);
                    std::string interp = prop.getMetaData().get("interpretation");
                    if(interp == "rgb")
                    {
                        Alembic::AbcCoreAbstract::DataType dType = prop.getDataType();
                        Alembic::Util::uint8_t extent = dType.getExtent();
                        Alembic::AbcCoreAbstract::ArraySamplePtr samp;
                        prop.get(samp);
                        QByteArray colorData((const char *)samp->getData(), samp->size() * 3 * sizeof(float));
                        colorDataBuffer->setData(colorData);
                        break; // set colors only once
                    }
                }
            }
        }

        // if needed, fill the buffer with a default color
        if(colorDataBuffer->data().isEmpty())
        {
            float* colors = new float[positions->size() * 3];
            for(int i = 0; i < positions->size() * 3; i++)
                colors[i] = 1.f;
            QByteArray colorData((const char *)colors, npoints * 3 * sizeof(float));
            colorDataBuffer->setData(colorData);
        }

        // colors buffer
        QAttribute *colorAttribute = new QAttribute;
        colorAttribute->setAttributeType(QAttribute::VertexAttribute);
        colorAttribute->setBuffer(colorDataBuffer);
        colorAttribute->setDataType(QAttribute::Float);
        colorAttribute->setDataSize(3);
        colorAttribute->setByteOffset(0);
        colorAttribute->setByteStride(3 * sizeof(float));
        colorAttribute->setCount(npoints);
        colorAttribute->setName(QAttribute::defaultColorAttributeName());
        customGeometry->addAttribute(colorAttribute);

        // add component
        customMeshRenderer->setInstanceCount(1);
        customMeshRenderer->setFirstVertex(0);
        customMeshRenderer->setFirstInstance(0);
        customMeshRenderer->setPrimitiveType(QGeometryRenderer::Points);
        customMeshRenderer->setGeometry(customGeometry);
        customMeshRenderer->setVertexCount(npoints);
        entity->addComponent(customMeshRenderer);
        entity->addComponent(_pointCloudMaterial);
    }
    else if(IXform::matches(md))
    {
        // get abc transform matrix
        IXform xform(iObj, kWrapExisting);
        XformSample xs;
        xform.getSchema().get(xs);
        mat *= xs.getMatrix();
        // set qt transform matrix
        Qt3DCore::QTransform *transform = new Qt3DCore::QTransform;
        QMatrix4x4 qmat(mat[0][0], mat[1][0], mat[2][0], mat[3][0], mat[0][1], mat[1][1],
                            mat[2][1], mat[3][1], mat[0][2], mat[1][2], mat[2][2], mat[3][2],
                            mat[0][3], mat[1][3], mat[2][3], mat[3][3]);
        transform->setMatrix(qmat);
        // apply it to a new entity
        entity = new QEntity(this);
        entity->addComponent(transform);
    }
    else if(ICamera::matches(md))
    {
        /*
        QCamera* camera = new QCamera(this);
        camera->setProjectionType(QCameraLens::PerspectiveProjection);
        camera->setAspectRatio(4.0f/3.0f);
        camera->setUpVector(QVector3D(0.0f, 1.0f, 0.0f));
        camera->setViewCenter(QVector3D(0.0f, 3.5f, 0.0f));
        camera->setPosition(QVector3D(0.0f, 3.5f, 25.0f));
        */

        // create a new geometry renderer
        QGeometryRenderer *customMeshRenderer = new QGeometryRenderer;
        QGeometry* customGeometry = new QGeometry;

        // vertices buffer
        QVector<float> points {
            0.f,  0.f,  0.f,  0.5,  0.f,  0.f,  0.f,  0.f,  0.f,  0.f,  0.5,  0.f,  0.f, 0.f,
            0.f,  0.f,  0.f,  0.5,  0.f,  0.f,  0.f,  -0.3, 0.2,  -0.3, 0.f,  0.f,  0.f, -0.3,
            -0.2, -0.3, 0.f,  0.f,  0.f,  0.3,  -0.2, -0.3, 0.f,  0.f,  0.f,  0.3,  0.2, -0.3,
            -0.3, 0.2,  -0.3, -0.3, -0.2, -0.3, -0.3, -0.2, -0.3, 0.3,  -0.2, -0.3, 0.3, -0.2,
            -0.3, 0.3,  0.2,  -0.3, 0.3,  0.2,  -0.3, -0.3, 0.2,  -0.3};
        QByteArray positionData((const char *)points.data(), points.size() * sizeof(float));
        QBuffer* vertexDataBuffer = new QBuffer(QBuffer::VertexBuffer);
        vertexDataBuffer->setData(positionData);
        QAttribute *positionAttribute = new QAttribute;
        positionAttribute->setAttributeType(QAttribute::VertexAttribute);
        positionAttribute->setBuffer(vertexDataBuffer);
        positionAttribute->setDataType(QAttribute::Float);
        positionAttribute->setDataSize(3);
        positionAttribute->setByteOffset(0);
        positionAttribute->setByteStride(3 * sizeof(float));
        positionAttribute->setCount(points.size() / 3);
        positionAttribute->setName(QAttribute::defaultPositionAttributeName());
        customGeometry->addAttribute(positionAttribute);

        // colors buffer
        QVector<float> colors {
            1.f, 0.f, 0.f, 1.f, 0.f, 0.f, 0.f, 1.f, 0.f, 0.f, 1.f, 0.f, 0.f, 0.f, 1.f, 0.f, 0.f,
            1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f,
            1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f,
            1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f};
        QByteArray colorData((const char *)colors.data(), colors.size() * sizeof(float));
        QBuffer* colorDataBuffer = new QBuffer(QBuffer::VertexBuffer);
        colorDataBuffer->setData(colorData);
        QAttribute *colorAttribute = new QAttribute;
        colorAttribute->setAttributeType(QAttribute::VertexAttribute);
        colorAttribute->setBuffer(colorDataBuffer);
        colorAttribute->setDataType(QAttribute::Float);
        colorAttribute->setDataSize(3);
        colorAttribute->setByteOffset(0);
        colorAttribute->setByteStride(3 * sizeof(float));
        colorAttribute->setCount(colors.size() / 3);
        colorAttribute->setName(QAttribute::defaultColorAttributeName());
        customGeometry->addAttribute(colorAttribute);

        // add component
        customMeshRenderer->setInstanceCount(1);
        customMeshRenderer->setFirstVertex(0);
        customMeshRenderer->setFirstInstance(0);
        customMeshRenderer->setPrimitiveType(QGeometryRenderer::Lines);
        customMeshRenderer->setGeometry(customGeometry);
        customMeshRenderer->setVertexCount(points.size() / 3);
        entity->addComponent(customMeshRenderer);
        entity->addComponent(_cameraMaterial);
    }

    // visit children
    for(size_t i = 0; i < iObj.getNumChildren(); i++)
        visitAbcObject(iObj.getChild(i), mat, entity);
}


// private
void AlembicEntity::createMaterials()
{
    using namespace Qt3DRender;
    using namespace Qt3DExtras;

    // camera material
    _cameraMaterial = new QPerVertexColorMaterial(this);

    // point cloud material
    _pointCloudMaterial = new QMaterial(this);
    QEffect* effect = new QEffect;
    QTechnique* technique = new QTechnique;
    QRenderPass* renderPass = new QRenderPass;
    QShaderProgram* shaderProgram = new QShaderProgram;

    // vertex shader
    shaderProgram->setVertexShaderCode(R"(#version 330 core
        uniform mat4 modelViewProjection;
        in vec3 vertexPosition;
        in vec3 vertexColor;
        out vec3 colors;
        void main(void)
        {
            gl_Position = modelViewProjection * vec4(vertexPosition, 1.0f);
            colors = vertexColor;
        }
    )");

    // fragment shader
    shaderProgram->setFragmentShaderCode(R"(#version 330 core
        in vec3 color;
        out vec4 fragColor;
        void main(void)
        {
            fragColor = vec4(color, 1.0);
        }
    )");

    // geometry shader
    shaderProgram->setGeometryShaderCode(R"(#version 330
        layout(points) in;
        layout(triangle_strip) out;
        layout(max_vertices = 4) out;
        uniform mat4 projectionMatrix;
        uniform float particleSize;
        in vec3 colors[];
        out vec3 color;
        void main(void)
        {
            vec4 right = vec4(0, particleSize, 0, 0);
            vec4 up = vec4(particleSize, 0, 0, 0);
            color = colors[0];
            gl_Position = gl_in[0].gl_Position - projectionMatrix*(right + up);
            EmitVertex();
            gl_Position = gl_in[0].gl_Position - projectionMatrix*(right - up);
            EmitVertex();
            gl_Position = gl_in[0].gl_Position + projectionMatrix*(right - up);
            EmitVertex();
            gl_Position = gl_in[0].gl_Position + projectionMatrix*(right + up);
            EmitVertex();
            EndPrimitive();
        }
    )");

    // particleSize uniform
    _particleSizeParameter->setName("particleSize");
    _particleSizeParameter->setValue(_particleSize);

    // build the material
    renderPass->setShaderProgram(shaderProgram);
    technique->addRenderPass(renderPass);
    effect->addTechnique(technique);
    _pointCloudMaterial->setEffect(effect);
    _pointCloudMaterial->addParameter(_particleSizeParameter);
}

} // namespace
