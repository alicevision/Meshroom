#include "UndoStack.hpp"

UndoStack::UndoStack(QObject* parent)
    : QObject(parent)
{
}

QObject* UndoStack::undoStack() const
{
    return _undoStack;
}

void UndoStack::setUndoStack(QObject* value)
{
    if(_undoStack == value)
        return;
    if(_undoStack)
        _undoStack->disconnect(this);
    _undoStack = static_cast<QUndoStack*>(value);
    connect(_undoStack, &QUndoStack::indexChanged, this, &UndoStack::rebuildModel);
    connect(_undoStack, &QUndoStack::indexChanged, this, &UndoStack::indexChanged);
    rebuildModel();
    Q_EMIT undoStackChanged();
}

int UndoStack::index() const
{
    return _undoStack->index();
}

void UndoStack::setIndex(int idx)
{
    if(index() == idx)
        return;
    _undoStack->setIndex(idx);
}

QQmlObjectListModel<UndoCommand>* UndoStack::commands()
{
    return &_commands;
}

void UndoStack::rebuildModel()
{
    if(_commands.count() == _undoStack->count())
        return;
    _commands.clear();
    for(int i = 0; i < _undoStack->count(); ++i)
    {
        auto* cmd = new UndoCommand(_undoStack->command(i), this);
        _commands.append(cmd);
    }
}
