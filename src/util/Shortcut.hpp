#pragma once

#include <QObject>
#include <QKeySequence>

namespace meshroom
{

class Shortcut : public QObject
{
    Q_OBJECT
    Q_PROPERTY(QVariant key READ key WRITE setKey NOTIFY keyChanged)

public:
    Shortcut(QObject* parent = 0);

public:
    QVariant key();
    void setKey(QVariant key);
    bool eventFilter(QObject* obj, QEvent* e) override;

signals:
    void keyChanged();
    void activated();
    void pressedAndHold();

private:
    QKeySequence _keySequence;
    bool _keypressAlreadySend;
};

} // namespace
