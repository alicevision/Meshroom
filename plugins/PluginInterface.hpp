#pragma once

#include <QString>
#include <Node.hpp>

class PluginInterface
{
public:
    virtual ~PluginInterface() = default;
    virtual QString name() = 0;
    virtual int major() = 0;
    virtual int minor() = 0;
    virtual QStringList nodeTypes() = 0;
    virtual dg::Ptr<dg::Node> createNode(const QString&, const QString&, dg::Graph&) = 0;
};

#define PluginInterface_iid "meshroom.PluginInterface/1.0"

Q_DECLARE_INTERFACE(PluginInterface, PluginInterface_iid)
