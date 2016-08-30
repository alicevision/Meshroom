#pragma once

#include "AlembicEntity.hpp"
#include <QtQml>
#include <QQmlExtensionPlugin>

namespace abcentity
{

class Qt3DAlembicEntityQmlPlugin : public QQmlExtensionPlugin
{
    Q_OBJECT
    Q_PLUGIN_METADATA(IID "qt3DAlembicEntity.qmlPlugin")

public:
    void initializeEngine(QQmlEngine* engine, const char* uri) override {}
    void registerTypes(const char* uri) override
    {
        Q_ASSERT(uri == QLatin1String("Qt3DAlembicEntity"));
        qmlRegisterType<AlembicEntity>(uri, 1, 0, "AlembicEntity");
    }
};

} // namespace
