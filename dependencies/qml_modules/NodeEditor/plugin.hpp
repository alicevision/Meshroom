#pragma once

#include <QtQml>
#include <QQmlExtensionPlugin>
#include "NodeModel.hpp"
#include "AttributeModel.hpp"

namespace nodeeditor
{

class NodeEditorQmlPlugin : public QQmlExtensionPlugin
{
    Q_OBJECT
    Q_PLUGIN_METADATA(IID "nodeeditor.qmlPlugin")

public:
    void initializeEngine(QQmlEngine* engine, const char* uri) override
    {
        NodeModel* model = new NodeModel();
        Node* node = new Node("node");
        model->addNode(node);

        // text
        Attribute* textfield = new Attribute();
        textfield->setValue("textfield");
        textfield->setKey("textfield");
        textfield->setName("textfield name");
        textfield->setTooltip("textfield tooltip");
        textfield->setType(Attribute::AttributeType::TEXTFIELD);
        node->attributes()->addAttribute(textfield);
        // slider
        Attribute* slider = new Attribute();
        slider->setValue(25);
        slider->setMin(0);
        slider->setMax(100);
        slider->setStep(5);
        slider->setKey("slider");
        slider->setName("slider name");
        slider->setTooltip("slider tooltip");
        slider->setType(Attribute::AttributeType::SLIDER);
        node->attributes()->addAttribute(slider);
        // slider
        Attribute* combobox = new Attribute();
        combobox->setValue("a");
        combobox->setKey("combo");
        combobox->setName("combo name");
        combobox->setTooltip("combo tooltip");
        combobox->setType(Attribute::AttributeType::COMBOBOX);
        combobox->setOptions({"a", "b", "c"});
        node->attributes()->addAttribute(combobox);
        // checkbox
        Attribute* checkbox = new Attribute();
        checkbox->setValue(true);
        checkbox->setKey("checkbox");
        checkbox->setName("checkbox name");
        checkbox->setTooltip("checkbox tooltip");
        checkbox->setType(Attribute::AttributeType::CHECKBOX);
        node->attributes()->addAttribute(checkbox);

        if(engine && engine->rootContext())
            engine->rootContext()->setContextProperty("_nodes", model);
    }
    void registerTypes(const char* uri) override
    {
        Q_ASSERT(uri == QLatin1String("NodeEditor"));
        qmlRegisterUncreatableType<Node>(uri, 1, 0, "Node",
                                         "type registration failed (nodeeditor::Node)");
        qmlRegisterUncreatableType<Attribute>(uri, 1, 0, "Attribute",
                                              "type registration failed (nodeeditor::Attribute)");
    }
};

} // namespace
