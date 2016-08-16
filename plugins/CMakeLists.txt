
# list subdirectories macro
macro(subdirlist result curdir)
    file(GLOB children RELATIVE ${curdir} ${curdir}/*)
    set(dirlist "")
    foreach(child ${children})
        if(IS_DIRECTORY ${curdir}/${child})
            list(APPEND dirlist ${child})
        endif()
    endforeach()
    set(${result} ${dirlist})
endmacro()


subdirlist(SUBDIRS ${CMAKE_CURRENT_SOURCE_DIR})
foreach(subdir ${SUBDIRS})
    string(TOUPPER ${subdir} dirname) # to upper
    set(WITH_${dirname}_PLUGIN OFF CACHE BOOL "Build ${dirname} plugin")
    if(WITH_${dirname}_PLUGIN)
        add_subdirectory(${subdir}) # add subdirectory
    endif()
endforeach()
