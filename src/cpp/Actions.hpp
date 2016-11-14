#pragma once

#include "Application.hpp"

namespace meshroom
{

struct EditAttributeAction
{
    static bool process(Graph* graph, QJsonObject& descriptor)
    {
        Q_CHECK_PTR(graph);
        using namespace dg;
        auto makeCoreAttribute = [&](const QVariant& attribute) -> dg::Ptr<dg::Attribute>
        {
            switch(attribute.type())
            {
                case QVariant::Bool:
                    return make_ptr<dg::Attribute>(attribute.toBool());
                case QVariant::Double:
                    return make_ptr<dg::Attribute>((float)attribute.toDouble());
                case QVariant::Int:
                    return make_ptr<dg::Attribute>(attribute.toInt());
                case QVariant::String:
                    return make_ptr<dg::Attribute>(attribute.toString().toStdString());
                default:
                    break;
            }
            return nullptr;
        };
        // read attribute description
        QString nodename = descriptor.value("node").toString(); // added dynamically
        QString plugname = descriptor.value("key").toString();
        QVariant value = descriptor.value("value").toVariant();
        if(!value.isValid()) // may happen, in case of a connected attribute
            return false;
        // retrieve the node
        auto& coreGraph = graph->coreGraph();
        auto coreNode = coreGraph.node(nodename.toStdString());
        if(!coreNode)
        {
            qCritical() << "unable to edit attribute"
                        << QString("%0::%1").arg(nodename).arg(plugname) << "- node not found";
            return false;
        }
        // edit the attribute value
        dg::AttributeList attributelist;
        if(value.type() == QVariant::List)
        {
            for(auto v : value.toList())
                attributelist.emplace_back(makeCoreAttribute(v));
        }
        else
            attributelist.emplace_back(makeCoreAttribute(value));
        if(!coreNode->setAttributes(plugname.toStdString(), attributelist))
        {
            qCritical() << "unable to edit attribute"
                        << QString("%0::%1").arg(nodename).arg(plugname)
                        << "- invalid attribute name or value type";
            return false;
        }
        return true;
    }
};

struct MoveNodeAction
{
    static bool process(Graph* graph, QJsonObject& descriptor)
    {
        Q_CHECK_PTR(graph);
        QString nodename = descriptor.value("name").toString();
        int x = descriptor.value("x").toInt();
        int y = descriptor.value("y").toInt();
        auto guiNodes = graph->nodes();
        auto modelIndex = guiNodes->index(guiNodes->rowIndex(nodename));
        return guiNodes->setData(modelIndex, QPoint(x, y),
                                 nodeeditor::NodeCollection::PositionRole);
    }
};

struct AddNodeAction
{
    static bool process(Graph* graph, QJsonObject& descriptor, QJsonObject& updatedDescriptor)
    {
        Q_CHECK_PTR(graph);
        // retrieve parent scene
        QObject* scene = graph->parent();
        Q_CHECK_PTR(scene);
        // retrieve parent application
        auto application = qobject_cast<Application*>(scene->parent());
        Q_CHECK_PTR(application);
        // create a new core node
        QString nodetype = descriptor.value("type").toString();
        QString nodename = descriptor.value("name").toString();
        auto coreNode = application->createNode(nodetype, nodename);
        if(!coreNode)
        {
            qCritical() << "unable to create a new" << nodetype << "node";
            return false;
        }
        // add the node to the graph
        auto& coreGraph = graph->coreGraph();
        if(!coreGraph.addNode(coreNode))
            return false;
        // warn in case the name changed
        QString realname = QString::fromStdString(coreNode->name);
        updatedDescriptor = descriptor;
        updatedDescriptor.insert("name", realname);

        // TODO
        // if(realname != nodename)
        //     Q_EMIT nodeNameChanged(nodename, realname);

        // set node attributes
        for(auto a : descriptor.value("inputs").toArray())
        {
            QJsonObject attributeDescriptor = a.toObject();
            attributeDescriptor.insert("node", realname); // add a reference to the node
            EditAttributeAction::process(graph, attributeDescriptor);
        }

        // move the node
        MoveNodeAction::process(graph, updatedDescriptor);
        return true;
    }
};

struct RemoveNodeAction
{
    static bool process(Graph* graph, QJsonObject& descriptor)
    {
        Q_CHECK_PTR(graph);
        if(!descriptor.contains("name"))
        {
            qCritical() << "unable to remove node: invalid node name";
            return false;
        }
        // retrieve the node to delete
        QString nodename = descriptor.value("name").toString();
        auto& coreGraph = graph->coreGraph();
        auto coreNode = coreGraph.node(nodename.toStdString());
        if(!coreNode)
        {
            qCritical() << "unable to remove node: node" << nodename << "not found";
            return false;
        }
        // delete the node
        return coreGraph.removeNode(coreNode);
    }
};

struct AddEdgeAction
{
    static bool process(Graph* graph, QJsonObject& descriptor)
    {
        Q_CHECK_PTR(graph);
        if(!descriptor.contains("source") || !descriptor.contains("target") ||
           !descriptor.contains("plug"))
        {
            qCritical() << "unable to connect nodes: invalid edge description";
            return false;
        }
        // retrieve source and target nodes
        QString sourcename = descriptor.value("source").toString();
        QString targetname = descriptor.value("target").toString();
        auto& coreGraph = graph->coreGraph();
        auto coreSourceNode = coreGraph.node(sourcename.toStdString());
        auto coreTargetNode = coreGraph.node(targetname.toStdString());
        if(!coreSourceNode || !coreTargetNode)
        {
            qCritical() << "unable to connect nodes: source/target node(s) not found";
            return false;
        }
        // retrieve target plug
        QString plugname = descriptor.value("plug").toString();
        auto corePlug = coreTargetNode->plug(plugname.toStdString());
        if(!corePlug)
        {
            qCritical() << "unable to connect nodes: plug" << plugname << "not found";
            return false;
        }
        // connect the nodes
        return coreGraph.connect(coreSourceNode->output, corePlug);
    }
};

struct RemoveEdgeAction
{
    static bool process(Graph* graph, QJsonObject& descriptor)
    {
        Q_CHECK_PTR(graph);
        if(!descriptor.contains("source") || !descriptor.contains("target") ||
           !descriptor.contains("plug"))
        {
            qCritical() << "unable to disconnect nodes: invalid edge description";
            return false;
        }
        // retrieve source and target nodes
        QString sourcename = descriptor.value("source").toString();
        QString targetname = descriptor.value("target").toString();
        auto& coreGraph = graph->coreGraph();
        auto coreSourceNode = coreGraph.node(sourcename.toStdString());
        auto coreTargetNode = coreGraph.node(targetname.toStdString());
        if(!coreSourceNode || !coreTargetNode)
        {
            qCritical() << "unable to disconnect nodes: invalid edge";
            return false;
        }
        // retrieve target plug
        QString plugname = descriptor.value("plug").toString();
        auto corePlug = coreTargetNode->plug(plugname.toStdString());
        if(!corePlug)
        {
            qCritical() << "unable to disconnect nodes: plug" << plugname << "not found";
            return false;
        }
        // disconnect the nodes
        return coreGraph.disconnect(coreSourceNode->output, corePlug);
    }
};

} // namespace
