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
    UndoStack(QObject* parent = nullptr);

public:
    QObject* undoStack() const;
    void setUndoStack(QObject* value);
    int index() const;
    void setIndex(int idx);
    QQmlObjectListModel<UndoCommand>* commands();
    void rebuildModel();

protected:
    Q_SIGNAL void undoStackChanged();
    Q_SIGNAL void indexChanged();

protected:
    QUndoStack* _undoStack = nullptr;
    QQmlObjectListModel<UndoCommand> _commands;
};
