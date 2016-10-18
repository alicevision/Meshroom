#include "Worker.hpp"
#include "Graph.hpp"
#include <QDir>
#include <QDebug>

using namespace dg;
namespace meshroom
{

Worker::Worker(Graph* graph)
    : _graph(graph)
{
}

void Worker::compute()
{
    Q_CHECK_PTR(_graph);

    // if the cache folder is not valid, abort
    if(!_graph->cacheUrl().isValid())
    {
        qCritical() << "invalid cache url";
        return;
    }

    // if the cache folder does not exist, create it
    QDir dir(_graph->cacheUrl().toLocalFile());
    if(!dir.exists())
        dir.mkpath(".");

    // in case the node name is empty, operate on graph leaves
    auto& dggraph = _graph->dggraph();
    if(_node.isEmpty())
    {
        NodeList leaves = dggraph.leaves();
        if(leaves.empty())
            return;
        _node = QString::fromStdString(leaves[0]->name); // FIXME first leaf
    }

    // instantiate a runner, depending on build mode
    switch(_mode)
    {
        case Mode::COMPUTE_LOCAL:
            _runner = new LocalComputeRunner();
            qInfo() << "Graph::compute (local) - starting from node" << _node;
            break;
        case Mode::COMPUTE_TRACTOR:
            _runner = new TractorComputeRunner();
            qInfo() << "Graph::compute (tractor) - starting from node" << _node;
            break;
        case Mode::PREPARE:
            _runner = new PrepareRunner();
            qInfo() << "Graph::prepare (local) - starting from node" << _node;
            break;
    }

    // callback, called several times by the runner
    auto status_callback = [&](const Node& node, Runner::NodeStatus status, const std::string& msg)
    {
        QString nodeName = QString::fromStdString(node.name);
        switch(status)
        {
            case Runner::NodeStatus::READY:
                Q_EMIT nodeStatusChanged(nodeName, "READY");
                break;
            case Runner::NodeStatus::WAITING:
                Q_EMIT nodeStatusChanged(nodeName, "WAITING");
                break;
            case Runner::NodeStatus::RUNNING:
                Q_EMIT nodeStatusChanged(nodeName, "RUNNING");
                break;
            case Runner::NodeStatus::ERROR:
                Q_EMIT nodeStatusChanged(nodeName, "ERROR");
                break;
            case Runner::NodeStatus::DONE:
                Q_EMIT nodeStatusChanged(nodeName, "DONE");
                break;
        }
        if(msg.empty())
            return;
        QDebug output = (status == Runner::NodeStatus::ERROR) ? qCritical() : qInfo();
        output << QString::fromStdString(msg);
    };

    // run
    try
    {
        _runner->registerCB(status_callback);
        _runner->operator()(dggraph, _node.toStdString());
    }
    catch(std::exception& e)
    {
        qCritical() << e.what();
    }

    // clean
    delete _runner;
    _runner = nullptr;
}

void Worker::killChildProcesses()
{
    if(!_runner)
        return;
    _runner->kill();
}

} // namespace
