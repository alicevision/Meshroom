#pragma once

#include <QtQml>
#include <QQmlExtensionPlugin>
#include "UndoStack.hpp"

#define FAIL_MSG(TYPE) "type registration failed (" #TYPE ")"

class UndoViewQmlPlugin : public QQmlExtensionPlugin
{
    Q_OBJECT
    Q_PLUGIN_METADATA(IID "undoView.qmlPlugin")

public:
    void initializeEngine(QQmlEngine* engine, const char* uri) override {}
    void registerTypes(const char* uri) override
    {
        Q_ASSERT(uri == QLatin1String("UndoView"));
        qmlRegisterType<UndoStack>(uri, 1, 0, "UndoStack");
        qmlRegisterUncreatableType<UndoCommand>(uri, 1, 0, "UndoCommand", FAIL_MSG(UndoCommand));
    }
};
