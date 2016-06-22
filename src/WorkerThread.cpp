#include "WorkerThread.hpp"
#include <QDebug>

using namespace dg;
namespace meshroom
{

WorkerThread::WorkerThread(QObject* parent, const QString& nodeName, Graph::BuildMode mode,
                           dg::Ptr<dg::Graph> graph)
    : QThread(parent)
    , _nodeName(nodeName)
    , _mode(mode)
    , _graph(graph)
{
}

void WorkerThread::run()
{
    qWarning() << "computing" << _nodeName;
    try
    {
        Runner* runner = nullptr;
        switch(_mode)
        {
            case Graph::LOCAL:
                runner = new LocalRunner();
                break;
            case Graph::TRACTOR:
                runner = new TractorRunner();
                break;
            default:
                break;
        }

        auto visited = [&](const std::string& node)
        {
            Q_EMIT nodeStatusChanged(QString::fromStdString(node), "WAITING");
        };
        auto computeStarted = [&](const std::string& node)
        {
            Q_EMIT nodeStatusChanged(QString::fromStdString(node), "RUNNING");
        };
        auto computeCompleted = [&](const std::string& node)
        {
            Q_EMIT nodeStatusChanged(QString::fromStdString(node), "DONE");
        };
        auto computeFailed = [&](const std::string& node)
        {
            Q_EMIT nodeStatusChanged(QString::fromStdString(node), "ERROR");
        };
        runner->registerOnVisitCB(visited);
        runner->registerOnComputeBeginCB(computeStarted);
        runner->registerOnComputeEndCB(computeCompleted);
        runner->registerOnErrorCB(computeFailed);

        runner->operator()(_graph, _nodeName.toStdString());
        delete runner;
    }
    catch(std::exception& e)
    {
        qCritical() << e.what();
    }
}

} // namespace
