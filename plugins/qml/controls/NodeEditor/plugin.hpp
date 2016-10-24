#pragma once

#include <QtQml>
#include <QQmlExtensionPlugin>
#include "AbstractGraph.hpp"
#include "AttributeCollection.hpp"

#define FAIL_MSG(TYPE) "type registration failed (" #TYPE ")"

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
        qmlRegisterUncreatableType<Node>(uri, 1, 0, "Node", FAIL_MSG(Node));
        qmlRegisterUncreatableType<Attribute>(uri, 1, 0, "Attribute", FAIL_MSG(Attribute));
        qmlRegisterUncreatableType<AttributeCollection>(uri, 1, 0, "AttributeCollection",
                                                        FAIL_MSG(AttributeCollection));
    }
};

} // namespace
