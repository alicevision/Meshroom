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
        }
        connect(this, &WorkerThread::processKilled, this, [&]()
                {
                    runner->kill();
                });
        runner->registerCB(
            [&](const dg::Node& node, dg::Runner::NodeStatus status, const std::string& msg)
            {
                QString nodeName = QString::fromStdString(node.name);
                switch(status)
                {
                    case dg::Runner::NodeStatus::READY:
                        Q_EMIT nodeStatusChanged(nodeName, "READY");
                        break;
                    case dg::Runner::NodeStatus::WAITING:
                        Q_EMIT nodeStatusChanged(nodeName, "WAITING");
                        break;
                    case dg::Runner::NodeStatus::RUNNING:
                        Q_EMIT nodeStatusChanged(nodeName, "RUNNING");
                        break;
                    case dg::Runner::NodeStatus::ERROR:
                        Q_EMIT nodeStatusChanged(nodeName, "ERROR");
                        break;
                    case dg::Runner::NodeStatus::DONE:
                        Q_EMIT nodeStatusChanged(nodeName, "DONE");
                        break;
                }
                if(!msg.empty())
                {
                    if(status == dg::Runner::NodeStatus::ERROR)
                        qCritical() << QString::fromStdString(msg);
                    else
                        qInfo() << QString::fromStdString(msg);
                }
            });
        runner->operator()(_graph, _nodeName.toStdString());
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
