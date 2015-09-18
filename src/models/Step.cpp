#include "Step.hpp"
#include <QJsonObject>

namespace mockup
{

Step::Step(const QString& name)
    : _name(name)
    , _attributes(new AttributeModel(this))
{
}

void Step::serializeToJSON(QJsonObject* stepsObject) const
{
    if(!stepsObject)
        return;
    QJsonObject stepObject;
    for(size_t i = 0; i < _attributes->rowCount(); i++)
    {
        QModelIndex id = _attributes->index(i, 0);
        Attribute* att = _attributes->data(id, AttributeModel::ModelDataRole).value<Attribute*>();
        att->serializeToJSON(&stepObject);
    }
    if(!stepObject.empty())
        stepsObject->insert(_name, stepObject);
}

void Step::deserializeFromJSON(const QJsonObject& stepsObject)
{
    if(!stepsObject.contains(_name))
        return;
    QJsonObject stepObject = stepsObject[_name].toObject();
    for(size_t i = 0; i < _attributes->rowCount(); i++)
    {
        QModelIndex id = _attributes->index(i, 0);
        Attribute* att = _attributes->data(id, AttributeModel::ModelDataRole).value<Attribute*>();
        if(!att)
            continue;
        att->deserializeFromJSON(stepObject);
    }
}

} // namespace
