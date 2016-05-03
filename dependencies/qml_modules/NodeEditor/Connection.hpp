#pragma once

#include <QObject>

namespace nodeeditor
{

class Connection : public QObject
{
    Q_OBJECT
    Q_PROPERTY(int sourceID READ sourceID WRITE setSourceID NOTIFY sourceIDChanged)
    Q_PROPERTY(int targetID READ targetID WRITE setTargetID NOTIFY targetIDChanged)
    Q_PROPERTY(int slotID READ slotID WRITE setSlotID NOTIFY slotIDChanged)

public:
    Connection() = default;
    Connection(const Connection& obj) = delete;
    Connection& operator=(Connection const&) = delete;

public:
    Q_SLOT const int& sourceID() const { return _sourceID; }
    Q_SLOT const int& targetID() const { return _targetID; }
    Q_SLOT const int& slotID() const { return _slotID; }
    Q_SLOT void setSourceID(const int&);
    Q_SLOT void setTargetID(const int&);
    Q_SLOT void setSlotID(const int&);
    Q_SIGNAL void sourceIDChanged();
    Q_SIGNAL void targetIDChanged();
    Q_SIGNAL void slotIDChanged();

public:
    void serializeToJSON(QJsonObject* obj) const;
    void deserializeFromJSON(const QJsonObject& obj);

private:
    int _sourceID;
    int _targetID;
    int _slotID;
};

} // namespace
