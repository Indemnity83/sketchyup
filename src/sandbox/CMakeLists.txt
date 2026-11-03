# R109.a (ADR 0183): the helper process sandbox. PR_SET_NO_NEW_PRIVS, a Landlock ruleset and a raw
# seccomp-bpf allow-list with a kill default, all written in-tree against the kernel's ABI. No
# dependency, and no Qt: the helpers that link it are plain C++.
# Elsewhere (macOS) every layer fails closed with ENOSYS, and the helpers refuse.
if(CMAKE_SYSTEM_NAME STREQUAL "Linux")
  add_library(sketchyup_sandbox ${SKETCHYUP_LIBRARY_TYPE}
    sandbox.cpp
    landlock.cpp
    seccomp.cpp)
else()
  add_library(sketchyup_sandbox ${SKETCHYUP_LIBRARY_TYPE}
    sandbox.cpp
    unsupported.cpp)
endif()
target_include_directories(sketchyup_sandbox PUBLIC ${PROJECT_SOURCE_DIR}/src)
target_compile_options(sketchyup_sandbox PRIVATE -Wall -Wextra -Wpedantic)
