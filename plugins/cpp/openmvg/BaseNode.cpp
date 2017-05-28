#include "BaseNode.hpp"


std::vector<dg::Command> BaseNode::prepare(dg::Cache &cache, dg::Environment &environment, bool &blocking)
{
    // Escape code to block visit and unset output plug cache
    auto clearAndBlockVisit = [&]() -> std::vector<Command> {
            blocking = true;
            cache.set(output, {});
            return {};
    };

    // Check all inputs for valid values
    // and store attributes names / values in a map for convenience
    std::map<std::string, AttributeList> in;
    for(const auto& input : inputs)
    {
        AttributeList attributes = cache.get(plug(input->name));
        if(attributes.empty())
        {
            // If an attribute is empty, (i.e connected input not calculated yet)
            // block the visit
            return clearAndBlockVisit();
        }
        in.emplace(input->name, attributes);
    }
    // Generate a UID for cache directory based on the values of sorted inputs
    AttributeList uid;
    for(const auto& attr : in)
        if(!std::binary_search(_notUID.begin(), _notUID.end(), attr.first))
            uid.insert(uid.end(), attr.second.begin(), attr.second.end());

    auto cacheDir = UIDcacheDir(type(), uid, environment);
    // Ensure the directory exists
    QDir().mkpath(cacheDir.c_str());

    // Call virtual prepare method
    AttributeList out;
    std::vector<std::vector<std::string>> commandsArgs;
    std::vector<std::string> execArgs = { "--compute", type(), "--" }; // meshroom arguments

    prepare(cacheDir, in, out, commandsArgs);

    // If no out attributes, can't continue
    if(out.empty())
        return clearAndBlockVisit();

    std::vector<Command> commands;
    // Block visit if any of the output attribute does not exist on disk
    blocking = std::any_of(out.begin(), out.end(),
                           [](Ptr<Attribute> attr){ return !attr->get<FileSystemRef>().exists(); });
    if(blocking)
    {
        // Build commands from meshroom args + provided arguments
        for(auto& args : commandsArgs)
        {
            args.insert(args.begin(), execArgs.begin(), execArgs.end());
            commands.emplace_back(args, environment);
        }
    }

    // Set output attributes
    cache.set(output, out);
    // Return the commands (empty if output is already computed)
    return commands;
}
