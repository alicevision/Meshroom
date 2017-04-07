#pragma once

#include <QObject>
#include <QUndoStack>

namespace meshroom
{

class UndoCommand; // forward declaration

class UndoStack : public QUndoStack
{
    Q_OBJECT
    Q_PROPERTY(bool isClean READ isClean NOTIFY isCleanChanged)

public:
    UndoStack(QObject* parent);

public:
    bool tryAndPush(UndoCommand*);
    Q_SIGNAL void isCleanChanged();
};

} // namespace
