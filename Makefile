##############################################################
#               CMake Project Wrapper Makefile               #
##############################################################

SHELL := /bin/bash
RM    := rm -rf

all: ./build/Makefile
	@ $(MAKE) -C build

./build/Makefile:
	@ (mkdir -p build && cd build >/dev/null 2>&1 && cmake ..)

format:
	@ find ./src -type f \( -iname \*.?pp \) -exec clang-format -i {} \;
	@ find ./dependencies -type f \( -iname \*.?pp \) -exec clang-format -i {} \;

confclean:
	@- (mkdir -p build && cd build >/dev/null 2>&1 && cmake .. >/dev/null 2>&1)
	@- $(MAKE) --silent -C build clean || true
	@- $(RM) ./build/Makefile
	@- $(RM) ./build/CMake*
	@- $(RM) ./build/cmake.*
	@- $(RM) ./build/*.cmake
	@- $(RM) ./build/*.txt

ifeq ($(filter $(MAKECMDGOALS),format confclean),)

    $(MAKECMDGOALS): ./build/Makefile
	@ $(MAKE) -C build $(MAKECMDGOALS)

endif
