#pragma once

#include <QObject>
#include <QtPlugin>
#include "PluginInterface.hpp"

class SamplePlugin : public QObject, PluginInterface
{
    Q_OBJECT
    Q_PLUGIN_METADATA(IID "meshroom.PluginInterface/1.0")
    Q_INTERFACES(PluginInterface)

public:
    QString name() override { return "Dummy"; }
    int major() override { return 1; }
    int minor() override { return 0; }
    QStringList nodeTypes() override { return {"DummyType"}; }
    // Ptr<Node> createNode(const QString& type, const QString& name)
    // {
    //     Ptr<Node> node;
    //     if(type == "DummyType")
    //         node = make_ptr<DummyNode>(name, *this);
    //     return node;
    // }
};
