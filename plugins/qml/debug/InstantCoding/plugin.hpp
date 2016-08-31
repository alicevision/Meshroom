#pragma once

#include <QtQml>
#include <QQmlExtensionPlugin>
#include "InstantCoding.hpp"

namespace instantcoding
{

class InstantCodingQmlPlugin : public QQmlExtensionPlugin
{
    Q_OBJECT
    Q_PLUGIN_METADATA(IID "instantCoding.qmlPlugin")

public:
    void registerTypes(const char* uri) override
    {
        Q_ASSERT(uri == QLatin1String("InstantCoding"));
    }
};

} // namespace
