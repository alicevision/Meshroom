#include "UndoStack.hpp"
#include "Commands.hpp"

namespace meshroom
{

UndoStack::UndoStack(QObject* parent)
    : QUndoStack(parent)
{
    connect(this, &QUndoStack::cleanChanged, this, &UndoStack::dirtyChanged);
}

bool UndoStack::tryAndPush(UndoCommand* command)
{
    if(command->redoImpl())
    {
        command->setEnabled(false);
        push(command);
        command->setEnabled(true);
        return true;
    }
    delete command;
    command = nullptr;
    return false;
}

} // namespace
