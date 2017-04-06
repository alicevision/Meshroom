#pragma once

#include <QString>
#include <QDebug>
#include <QProcess>
#include <iostream>

struct PluginToolBox
{
    static int executeProcess(const QString& processName,
                               const std::vector<std::string>& arguments)
    {
        // arguments to qlist
        QStringList qarguments;
        for(auto& arg : arguments)
            qarguments.append(QString::fromStdString(arg));

        // setup qprocess
        QProcess process;
        process.setProgram(processName);
        process.setArguments(qarguments);

        // add standard error/output callbacks
        auto printOutput = [&]()
        {
            std::cout << qPrintable(process.readAllStandardOutput());
        };
        auto printError = [&]()
        {
            std::cerr << qPrintable(process.readAllStandardError());
        };
        process.connect(&process, &QProcess::readyReadStandardOutput, printOutput);
        process.connect(&process, &QProcess::readyReadStandardError, printError);

        // print the full commandline
        QString fullcommand = process.program();
        for(auto& arg : qarguments)
        {
            fullcommand.append(" ");
            fullcommand.append(arg);
        }
        qDebug().noquote() << fullcommand;

        // start process and wait (block) until the end
        process.start();
        if(!process.waitForFinished(-1))
        {
            qCritical() << "ERROR: " << process.errorString();
        }
        if(process.exitCode() != 0)
        {
            QString errorMessage = QString("%1 (exit code: %2)").arg(process.errorString()).arg(process.exitCode());
            throw std::runtime_error(errorMessage.toStdString());
        }
        return process.exitCode();
    }
};
