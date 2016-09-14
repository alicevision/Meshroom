#include "AlembicEntity.hpp"
#include "CameraLocatorEntity.hpp"
#include "PointCloudEntity.hpp"
#include <Qt3DRender/QEffect>
#include <Qt3DRender/QTechnique>
#include <Qt3DRender/QRenderPass>
#include <Qt3DRender/QShaderProgram>
#include <Qt3DRender/QObjectPicker>
#include <Qt3DRender/QPickEvent>
#include <Qt3DExtras/QPerVertexColorMaterial>

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

void AlembicEntity::setLocatorScale(const float& value)
{
    if(_locatorScale == value)
        return;
    _locatorScale = value;
    for(auto entity : findChildren<CameraLocatorEntity*>())
    {
        for(auto transform : entity->findChildren<Qt3DCore::QTransform*>())
            transform->setScale(value);
    }
    Q_EMIT locatorScaleChanged();
}

// private
void AlembicEntity::createMaterials()
{
    using namespace Qt3DRender;
    using namespace Qt3DExtras;

    _cloudMaterial = new QMaterial(this);
    _cameraMaterial = new QPerVertexColorMaterial(this);

    // configure cloud material
    QEffect* effect = new QEffect;
    QTechnique* technique = new QTechnique;
    QRenderPass* renderPass = new QRenderPass;
    QShaderProgram* shaderProgram = new QShaderProgram;

    // set vertex shader
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

    // set fragment shader
    shaderProgram->setFragmentShaderCode(R"(#version 330 core
        in vec3 color;
        out vec4 fragColor;
        void main(void)
        {
            fragColor = vec4(color, 1.0);
        }
    )");

    // set geometry shader
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

    // add a particleSize uniform
    _particleSizeParameter->setName("particleSize");
    _particleSizeParameter->setValue(_particleSize);
    _cloudMaterial->addParameter(_particleSizeParameter);

    // build the material
    renderPass->setShaderProgram(shaderProgram);
    technique->addRenderPass(renderPass);
    effect->addTechnique(technique);
    _cloudMaterial->setEffect(effect);
}

// private
void AlembicEntity::loadAbcArchive()
{
    if(!_url.isValid())
        return;

    using namespace Qt3DRender;
    using namespace Alembic::Abc;
    using namespace Alembic::AbcGeom;

    // clear entity (remove direct children & all components)
    auto entities = findChildren<QEntity*>("", Qt::FindDirectChildrenOnly);
    for(auto entity : entities)
    {
        entity->setParent((QNode*)nullptr);
        delete entity;
    }
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
    visitAbcObject(archive.getTop(), xformMat);

    auto onPicked = [&](QPickEvent* pick)
    {
        auto picker = (QObjectPicker*)sender();
        for(auto e : picker->entities())
        {
            for(auto c : e->components())
            {
                if(c->isEnabled() && c->inherits("Qt3DCore::QTransform"))
                {
                    Q_EMIT objectPicked(qobject_cast<Qt3DCore::QTransform*>(c));
                    break;
                }
            }
        }
    };

    for(auto picker : findChildren<QObjectPicker*>())
        QObject::connect(picker, &QObjectPicker::clicked, this, onPicked);
}

// private
void AlembicEntity::visitAbcObject(Alembic::Abc::IObject iObj, Alembic::Abc::M44d mat)
{
    using namespace Alembic::Abc;
    using namespace Alembic::AbcGeom;

    const MetaData& md = iObj.getMetaData();
    if(IPoints::matches(md))
    {
        auto cloud = new PointCloudEntity(this);
        cloud->setData(iObj);
        cloud->setTransform(mat);
        cloud->addComponent(_cloudMaterial);
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
        auto cameraLocator = new CameraLocatorEntity(this);
        cameraLocator->setTransform(mat);
        cameraLocator->addComponent(_cameraMaterial);
    }

    // visit children
    for(size_t i = 0; i < iObj.getNumChildren(); i++)
        visitAbcObject(iObj.getChild(i), mat);
}

} // namespace
