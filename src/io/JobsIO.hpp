#pragma once

namespace meshroom
{

class Job; // forward declaration

class JobsIO
{
public:
    static void load(Job& job);
    static bool save(Job& job);
};

} // namespace
