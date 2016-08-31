#pragma once

#include <QObject>
#include <QtPlugin>
#include "PluginInterface.hpp"
#include "nodes/DummyNode.hpp"

class DummyPlugin : public QObject, PluginInterface
{
    Q_OBJECT
    Q_PLUGIN_METADATA(IID "meshroom.PluginInterface/1.0" FILE "plugin.json")
    Q_INTERFACES(PluginInterface)

public:
    dg::Ptr<dg::Node> createNode(const QString& type, const QString& name) override
    {
        using namespace dg;
        Ptr<Node> node = nullptr;
        if(type == "Dummy")
            node = make_ptr<DummyNode>(name.toStdString());
        return node;
    }
};
