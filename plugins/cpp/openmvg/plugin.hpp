#pragma once

#include <QObject>
#include <QtPlugin>
#include "PluginInterface.hpp"
#include "nodes/AlembicExport.hpp"
#include "nodes/ExifExtraction.hpp"
#include "nodes/FeatureExtraction.hpp"
#include "nodes/FeatureMatching.hpp"
#include "nodes/ImageListing.hpp"
#include "nodes/Localization.hpp"
#include "nodes/StructureFromMotion.hpp"
#include "nodes/Voctree.hpp"

class OpenMVGPlugin : public QObject, PluginInterface
{
    Q_OBJECT
    Q_PLUGIN_METADATA(IID "meshroom.PluginInterface/1.0" FILE "plugin.json")
    Q_INTERFACES(PluginInterface)

public:
    dg::Ptr<dg::Node> createNode(const QString& type, const QString& name) override
    {
        using namespace dg;
        Ptr<Node> node = nullptr;
        if(type == "openmvg.AlembicExport")
            node = make_ptr<AlembicExport>(name.toStdString());
        if(type == "openmvg.ExifExtraction")
            node = make_ptr<ExifExtraction>(name.toStdString());
        if(type == "openmvg.FeatureExtraction")
            node = make_ptr<FeatureExtraction>(name.toStdString());
        if(type == "openmvg.FeatureMatching")
            node = make_ptr<FeatureMatching>(name.toStdString());
        if(type == "openmvg.ImageListing")
            node = make_ptr<ImageListing>(name.toStdString());
        if(type == "openmvg.Localization")
            node = make_ptr<Localization>(name.toStdString());
        if(type == "openmvg.StructureFromMotion")
            node = make_ptr<StructureFromMotion>(name.toStdString());
        if(type == "openmvg.Voctree")
            node = make_ptr<Voctree>(name.toStdString());
        return node;
    }
};
