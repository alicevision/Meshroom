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

    // get dg graph & cache
    auto& dggraph = _graph->coreGraph();
    auto& dgcache = _graph->coreCache();
    auto& dgenvironment = _graph->coreEnvironment();

    // in case the node name is empty, operate on graph leaves
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

    try
    {
        _runner->onStatusChanged = onStatusChanged;
        _runner->operator()(dggraph, dgcache, dgenvironment, _node.toStdString());
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
