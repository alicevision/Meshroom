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
        switch(_mode)
        {
            case Graph::LOCAL:
            {
                LocalRunner runner;
                auto visitStarted = [&](const std::string& node)
                {
                    Q_EMIT nodeVisitStarted(QString::fromStdString(node));
                };
                auto visitCompleted = [&](const std::string& node)
                {
                    Q_EMIT nodeVisitCompleted(QString::fromStdString(node));
                };
                auto computeStarted = [&](const std::string& node)
                {
                    Q_EMIT nodeComputeStarted(QString::fromStdString(node));
                };
                auto computeCompleted = [&](const std::string& node)
                {
                    Q_EMIT nodeComputeCompleted(QString::fromStdString(node));
                };
                auto computeFailed = [&](const std::string& node)
                {
                    Q_EMIT nodeComputeFailed(QString::fromStdString(node));
                };
                runner.registerOnVisitBeginCB(visitStarted);
                runner.registerOnVisitEndCB(visitCompleted);
                runner.registerOnComputeBeginCB(computeStarted);
                runner.registerOnComputeEndCB(computeCompleted);
                runner.registerOnErrorCB(computeFailed);
                runner(_graph, _nodeName.toStdString());
                break;
            }
            case Graph::TRACTOR:
            {
                TractorRunner runner;
                runner(_graph, _nodeName.toStdString());
                break;
            }
            default:
                break;
        }
    }
    catch(std::exception& e)
    {
        qCritical() << e.what();
    }
}

} // namespace
