#include "WorkerThread.hpp"
#include <QDebug>

using namespace dg;
namespace meshroom
{

WorkerThread::WorkerThread(QObject* parent, const QString& node, Graph::BuildMode mode,
                           Ptr<dg::Graph> graph)
    : QThread(parent)
    , _node(node)
    , _mode(mode)
    , _graph(graph)
{
}

void WorkerThread::run()
{
    // instantiate a runner, depending on build mode
    Runner* runner = nullptr;
    switch(_mode)
    {
        case Graph::COMPUTE_LOCAL:
            runner = new LocalComputeRunner();
            break;
        case Graph::COMPUTE_TRACTOR:
            runner = new TractorComputeRunner();
            break;
        case Graph::PREPARE:
            runner = new PrepareRunner();
            break;
    }

    // in case the node name is empty, operate on graph leaves
    if(_node.isEmpty())
    {
        NodeList leaves = _graph->leaves();
        if(leaves.empty())
            return;
        _node = QString::fromStdString(leaves[0]->name); // FIXME first leaf
    }

    // callback, called on thread::terminate
    auto kill_callback = [&]()
    {
        runner->kill();
    };

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
        if(!msg.empty())
        {
            if(status == Runner::NodeStatus::ERROR)
                qCritical() << QString::fromStdString(msg);
            else
                qInfo() << QString::fromStdString(msg);
        }
    };

    try
    {
        // qt callback
        connect(this, &WorkerThread::processKilled, this, kill_callback);
        // dg callback
        runner->registerCB(status_callback);
        // run
        runner->operator()(_graph, _node.toStdString());
        delete runner;
    }
    catch(std::exception& e)
    {
        qCritical() << e.what();
    }
}

void WorkerThread::kill()
{
    Q_EMIT processKilled();
    terminate();
    wait();
}

} // namespace
