#pragma once

#include "PluginToolBox.hpp"
#include <dglib/dg.hpp>
#include <QDir>

using namespace dg;

/**
 * @brief Base class for simple nodes executing an external process.
 */
class BaseNode : public Node {

public:
    /**
     * BaseNode constructor
     *
     * @param nodeName the name of the node
     * @param executable the external process to launch at 'compute'
     */
    BaseNode(std::string nodeName, std::string executable):
      Node(nodeName)
      , _executable(executable)
    {
    }

    /**
     * @brief Implementation of dg::Node::prepare setuping everything before calling
     *        the higher-level BaseNode::prepare virtual method.
     */
    std::vector<Command> prepare(Cache& cache, Environment& environment, bool& blocking) override;

    /// Implementation of dg::Node::compute calling the executable given at ctor with
    /// commands arguments from BaseNode::prepare.
    inline void compute(const std::vector<std::string>& args) const override
    {
        PluginToolBox::executeProcess(_executable.c_str(), args);
    }

protected:

    /**
     * @brief Register an input plug of type T.
     * @param name the name of the plug
     * @param impactCacheDir whether its value impacts the cache directory name (default: true)
     */
    template<typename T>
    void registerInput(const std::string& name, bool impactCacheDir=true)
    {
        inputs.emplace_back(make_ptr<Plug>(std::type_index(typeid(T)), name, *this));
        if(!impactCacheDir)
            _notUID.emplace_back(name);
    }

    /**
     * @brief Register the output plug of type T.
     * @param name the name of the plug
     */
    template<typename T>
    void registerOutput(const std::string& name)
    {
        output = make_ptr<Plug>(std::type_index(typeid(T)), name, *this);
    }

    /**
     * @brief Higher-level 'prepare' method. Implement in subclasses.
     *
     * @param cacheDir absolute path to the cache directory for the current node based on input attributes
     * @param in input attributes map (plugName:value)
     * @param out output attributes. Expected to be FileSystemRefs.
     *        If empty, visit will be blocked.
     *        If any output is missing on disk, appropriate commands will be generated.
     * @param commandsArgs the list of commands arguments to create output attributes
     */
    virtual void prepare(const std::string& cacheDir,
                         const std::map<std::string, AttributeList>& in,
                         AttributeList& out,
                         std::vector<std::vector<std::string>>& commandsArgs) = 0;

    /**
     * @brief Generate a unique cache directory based on node type and 'attributes' values.
     * @return cache directory (no trailing '/')
     **/
    static std::string UIDcacheDir(std::string nodeType,
                                   const AttributeList& attributes,
                                   Environment& env)
    {
        // Turn '.' into '_' to avoid '.' in file paths
        std::string type_ = QString(nodeType.c_str()).replace(".", "_").toStdString();
        std::string outDir = env.get(dg::Environment::Key::CACHE_DIRECTORY) + "/" + type_;
        outDir = QDir::cleanPath(outDir.c_str()).toStdString() + "/";
        outDir += std::to_string(UID(nodeType, attributes));

        return outDir;
    }

protected:
    std::string _executable = "";

private:
    std::vector<std::string> _notUID;
};
