cmake_minimum_required(VERSION 3.10)
project(QuadrotorPlanner)

# Enable C++17
enable_language(CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Add OMPL config path (if installed)
set(CMAKE_PREFIX_PATH "${CMAKE_PREFIX_PATH};$ENV{HOME}/ompl-install/share/ompl")

# Boost from conda
set(BOOST_ROOT "$ENV{CONDA_PREFIX}")
set(BOOST_INCLUDEDIR "$ENV{CONDA_PREFIX}/include")
set(BOOST_LIBRARYDIR "$ENV{CONDA_PREFIX}/lib")
set(Boost_NO_SYSTEM_PATHS ON)  # Force CMake to ignore system boost

# Include paths
include_directories(
    $ENV{HOME}/ompl-install/include/ompl-1.7
    /usr/include/eigen3
    ${CMAKE_SOURCE_DIR}/include
    ${CMAKE_SOURCE_DIR}/src
    ${CMAKE_SOURCE_DIR}/other_stuff

    # ✅ Include OMPL.app headers (not installed version)
    $ENV{HOME}/omplapp/src

    # ✅ Correct path for generated omplapp/config.h
    $ENV{HOME}/omplapp/build/Release/src
)

# Boost
find_package(Boost REQUIRED COMPONENTS filesystem system serialization)
include_directories(${Boost_INCLUDE_DIRS})
link_directories(${Boost_LIBRARY_DIRS})

# Python and NumPy
find_package(Python3 REQUIRED COMPONENTS Development NumPy)
include_directories(${Python3_INCLUDE_DIRS} ${Python3_NumPy_INCLUDE_DIRS})

# OMPL & FCL
find_package(ompl REQUIRED)
find_package(fcl REQUIRED)

# OpenMP
find_package(OpenMP REQUIRED)

# TEMP FIX for broken OMPL config file
set(OMPL_LIBRARY_DIRS "$ENV{HOME}/ompl-install/lib")
link_directories(
    ${OMPL_LIBRARY_DIRS}
    $ENV{HOME}/omplapp/build/Release/lib
    $ENV{HOME}/ccd-install/lib
)

# Executable
add_executable(PayloadFourDrones src/PayloadFourDemo.cpp src/PayloadFourDrones.cpp)

# Link libraries
target_link_libraries(PayloadFourDrones PRIVATE
    ompl ompl_app_base fcl
    Boost::filesystem Boost::system Boost::serialization
    Python3::Python Python3::NumPy
    OpenMP::OpenMP_CXX
    stdc++fs
)

# Include directories for the executable
target_include_directories(PayloadFourDrones PRIVATE
    ${OMPL_INCLUDE_DIRS}
    ${fcl_INCLUDE_DIRS}
    ${Boost_INCLUDE_DIRS}
    ${Python3_INCLUDE_DIRS}
    ${Python3_NumPy_INCLUDE_DIRS}
    ${CMAKE_SOURCE_DIR}/include
    $ENV{HOME}/omplapp/src
    $ENV{HOME}/omplapp/build/Release/src
)

# ✅ Include paths for conda-installed GCC 12.2.0 (for ostream.tcc etc.)
target_include_directories(PayloadFourDrones PRIVATE
    $ENV{CONDA_PREFIX}/lib/gcc/x86_64-conda-linux-gnu/12.2.0/include/c++
    $ENV{CONDA_PREFIX}/lib/gcc/x86_64-conda-linux-gnu/12.2.0/include/c++/x86_64-conda-linux-gnu
)

# Build type
set(CMAKE_BUILD_TYPE Debug)

