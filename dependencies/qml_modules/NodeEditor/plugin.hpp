#pragma once

#include <QtQml>
#include <QQmlExtensionPlugin>
#include "NodeModel.hpp"
#include "ConnectionModel.hpp"
#include "AttributeModel.hpp"

namespace nodeeditor
{

class NodeEditorQmlPlugin : public QQmlExtensionPlugin
{
    Q_OBJECT
    Q_PLUGIN_METADATA(IID "nodeeditor.qmlPlugin")

public:
    void initializeEngine(QQmlEngine* engine, const char* uri) override {}
    void registerTypes(const char* uri) override
    {
        Q_ASSERT(uri == QLatin1String("NodeEditor"));
        qmlRegisterType<NodeModel>(uri, 1, 0, "NodeModel");
        qmlRegisterType<ConnectionModel>(uri, 1, 0, "ConnectionModel");
        qmlRegisterUncreatableType<Attribute>(uri, 1, 0, "Attribute",
                                              "type registration failed (nodeeditor::Attribute)");
    }
};

} // namespace
