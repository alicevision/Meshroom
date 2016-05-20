#pragma once

#include <QObject>
#include <QtPlugin>
#include <nodes/FeatureExtraction.hpp>
#include <nodes/FeatureMatching.hpp>
#include <nodes/ImageListing.hpp>
#include <nodes/PlyExport.hpp>
#include <nodes/StructureFromMotion.hpp>
#include "PluginInterface.hpp"

class TheiaPlugin : public QObject, PluginInterface
{
    Q_OBJECT
    Q_PLUGIN_METADATA(IID "meshroom.PluginInterface/1.0" FILE "plugin.json")
    Q_INTERFACES(PluginInterface)

public:
    dg::Ptr<dg::Node> createNode(const QString& type, const QString& name) override
    {
        using namespace dg;
        Ptr<Node> node;
        if(type == "FeatureExtraction")
            node = make_ptr<FeatureExtraction>(name.toStdString());
        else if(type == "FeatureMatching")
            node = make_ptr<FeatureMatching>(name.toStdString());
        else if(type == "ImageListing")
            node = make_ptr<ImageListing>(name.toStdString());
        else if(type == "PlyExport")
            node = make_ptr<PlyExport>(name.toStdString());
        else if(type == "StructureFromMotion")
            node = make_ptr<StructureFromMotion>(name.toStdString());
        return node;
    }
};
