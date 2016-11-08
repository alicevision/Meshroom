#pragma once

#include "QQmlObjectListModel.hpp"
#include <QObject>
#include <QUndoStack>

class UndoCommand : public QObject
{
    Q_OBJECT
    Q_PROPERTY(QString text READ text CONSTANT)

public:
    UndoCommand(const QUndoCommand* command, QObject* parent = nullptr)
        : QObject(parent)
        , _undoCommand(command)
    {
    }

    QString text() const { return _undoCommand->text(); }

protected:
    const QUndoCommand* _undoCommand;
};

class UndoStack : public QObject
{
    Q_OBJECT

    Q_PROPERTY(QObject* undoStack READ undoStack WRITE setUndoStack NOTIFY undoStackChanged)
    Q_PROPERTY(QObject* commands READ commands CONSTANT)
    Q_PROPERTY(int index READ index WRITE setIndex NOTIFY indexChanged)

public:
    UndoStack(QObject* parent = nullptr)
        : QObject(parent)
    {
    }

    QObject* undoStack() const { return _undoStack; }

    void setUndoStack(QObject* value)
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

    int index() const { return _undoStack->index(); }

    void setIndex(int idx)
    {
        if(index() == idx)
            return;
        _undoStack->setIndex(idx);
    }

    void rebuildModel()
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

    QQmlObjectListModel<UndoCommand>* commands() { return &_commands; }

Q_SIGNALS :
    void undoStackChanged();
    void indexChanged();

protected:
    QUndoStack* _undoStack = nullptr;
    QQmlObjectListModel<UndoCommand> _commands;
};
