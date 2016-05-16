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
    dg::Ptr<dg::Node> createNode(const QString& type, const QString& name,
                                 dg::Graph& graph) override
    {
        using namespace dg;
        Ptr<Node> node;
        if(type == "FeatureExtraction")
            node = make_ptr<FeatureExtraction>(name.toStdString(), graph);
        else if(type == "FeatureMatching")
            node = make_ptr<FeatureMatching>(name.toStdString(), graph);
        else if(type == "ImageListing")
            node = make_ptr<ImageListing>(name.toStdString(), graph);
        else if(type == "PlyExport")
            node = make_ptr<PlyExport>(name.toStdString(), graph);
        else if(type == "StructureFromMotion")
            node = make_ptr<StructureFromMotion>(name.toStdString(), graph);
        return node;
    }
};
