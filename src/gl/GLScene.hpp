#pragma once

#include <memory>
#include "GLDrawable.hpp"

namespace meshroom
{

typedef std::vector<std::unique_ptr<GLDrawable>> GLScene;

} // namespace
