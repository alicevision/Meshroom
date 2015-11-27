#pragma once

#include <QtQml>
#include <QQmlExtensionPlugin>
#include "Shortcut.hpp"

namespace shortcut
{

class GlobalShortcutQmlPlugin : public QQmlExtensionPlugin
{
    Q_OBJECT
    Q_PLUGIN_METADATA(IID "globalShortcut.qmlPlugin")

public:
    void initializeEngine(QQmlEngine* engine, const char* uri) override
    {
    }
    void registerTypes(const char* uri) override
    {
        Q_ASSERT(uri == QLatin1String("GlobalShortcut"));
        qmlRegisterType<Shortcut>(uri, 1, 0, "Shortcut");
    }
};

} // namespace
