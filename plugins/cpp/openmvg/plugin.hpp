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
        if(type == "AlembicExport")
            node = make_ptr<AlembicExport>(name.toStdString());
        if(type == "ExifExtraction")
            node = make_ptr<ExifExtraction>(name.toStdString());
        if(type == "FeatureExtraction")
            node = make_ptr<FeatureExtraction>(name.toStdString());
        if(type == "FeatureMatching")
            node = make_ptr<FeatureMatching>(name.toStdString());
        if(type == "ImageListing")
            node = make_ptr<ImageListing>(name.toStdString());
        if(type == "Localization")
            node = make_ptr<Localization>(name.toStdString());
        if(type == "StructureFromMotion")
            node = make_ptr<StructureFromMotion>(name.toStdString());
        if(type == "Voctree")
            node = make_ptr<Voctree>(name.toStdString());
        return node;
    }
};
