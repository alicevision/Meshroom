#!/bin/bash
find ./src -type f \( -iname \*.?pp \) -exec clang-format -i {} \;
