#include "Shortcut.hpp"
#include <QKeyEvent>
#include <QCoreApplication>

namespace shortcut
{

Shortcut::Shortcut(QObject* parent)
    : QObject(parent)
    , _keySequence()
    , _keypressAlreadySend(false)
{
    qApp->installEventFilter(this);
}

QVariant Shortcut::key()
{
    return _keySequence;
}

void Shortcut::setKey(QVariant key)
{
    QKeySequence newKey = key.value<QKeySequence>();
    if(_keySequence != newKey)
    {
        _keySequence = key.value<QKeySequence>();
        Q_EMIT keyChanged();
    }
}

bool Shortcut::eventFilter(QObject* obj, QEvent* e)
{
    if(e->type() == QEvent::KeyPress && !_keySequence.isEmpty())
    {
        QKeyEvent* keyEvent = static_cast<QKeyEvent*>(e);
        if(keyEvent->key() >= Qt::Key_Shift && keyEvent->key() <= Qt::Key_Alt)
            return QObject::eventFilter(obj, e);
        int keyInt = keyEvent->modifiers() + keyEvent->key();
        if(!_keypressAlreadySend && QKeySequence(keyInt) == _keySequence)
        {
            _keypressAlreadySend = true;
            Q_EMIT activated();
        }
    }
    else if(e->type() == QEvent::KeyRelease)
        _keypressAlreadySend = false;
    return QObject::eventFilter(obj, e);
}

} // namespace
