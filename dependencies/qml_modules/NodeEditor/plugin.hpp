#pragma once

#include <QtQml>
#include <QQmlExtensionPlugin>
#include "NodeModel.hpp"
#include "ConnectionModel.hpp"
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
        NodeModel* nodemodel = new NodeModel();
        ConnectionModel* connectionmodel = new ConnectionModel();

        Node* node1 = new Node("node1");
        Node* node2 = new Node("node2");
        nodemodel->addNode(node1);
        nodemodel->addNode(node2);

        // text
        Attribute* textfield = new Attribute();
        textfield->setValue("textfield");
        textfield->setKey("textfield");
        textfield->setName("textfield name");
        textfield->setTooltip("textfield tooltip");
        textfield->setType(Attribute::AttributeType::TEXTFIELD);
        node1->inputs()->addAttribute(textfield);
        node2->inputs()->addAttribute(textfield);
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
        node1->inputs()->addAttribute(slider);
        // slider
        Attribute* combobox = new Attribute();
        combobox->setValue("a");
        combobox->setKey("combo");
        combobox->setName("combo name");
        combobox->setTooltip("combo tooltip");
        combobox->setType(Attribute::AttributeType::COMBOBOX);
        combobox->setOptions({"a", "b", "c"});
        node1->inputs()->addAttribute(combobox);
        // checkbox
        Attribute* checkbox = new Attribute();
        checkbox->setValue(true);
        checkbox->setKey("checkbox");
        checkbox->setName("checkbox name");
        checkbox->setTooltip("checkbox tooltip");
        checkbox->setType(Attribute::AttributeType::CHECKBOX);
        node1->inputs()->addAttribute(checkbox);

        // connections
        Connection* connection = new Connection();
        connection->setSourceID(0);
        connection->setTargetID(1);
        connection->setSlotID(0);
        connectionmodel->addConnection(connection);

        if(engine && engine->rootContext())
        {
            engine->rootContext()->setContextProperty("_nodes", nodemodel);
            engine->rootContext()->setContextProperty("_connections", connectionmodel);
        }
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
