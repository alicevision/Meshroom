#pragma once

#include <QtQml>
#include <QQmlExtensionPlugin>
#include "Graph.hpp"

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
        qmlRegisterType<Graph>(uri, 1, 0, "Graph");
        qmlRegisterUncreatableType<NodeCollection>(uri, 1, 0, "NodeCollection",
                                                   "type registration failed (NodeCollection)");
        qmlRegisterUncreatableType<EdgeCollection>(uri, 1, 0, "EdgeCollection",
                                                   "type registration failed (EdgeCollection)");
        qmlRegisterUncreatableType<AttributeCollection>(
            uri, 1, 0, "AttributeCollection", "type registration failed (AttributeCollection)");
        qmlRegisterUncreatableType<Attribute>(uri, 1, 0, "Attribute",
                                              "type registration failed (Attribute)");
        qmlRegisterUncreatableType<Node>(uri, 1, 0, "Node", "type registration failed (Node)");
    }
};

} // namespace
