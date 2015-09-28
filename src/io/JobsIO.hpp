#pragma once

namespace mockup
{

class Job; // forward declaration

class JobsIO
{
public:
    static void load(Job& job);
    static bool save(Job& job);
};

} // namespace
