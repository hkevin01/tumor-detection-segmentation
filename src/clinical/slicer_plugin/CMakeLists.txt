cmake_minimum_required(VERSION 3.16.3...3.19.7 FATAL_ERROR)

project(TumorSegmentationAI)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE
    "https://github.com/hkevin01/tumor-detection-segmentation")
set(EXTENSION_CATEGORY "Segmentation")
set(EXTENSION_CONTRIBUTORS "Medical Imaging AI Platform Team")
set(EXTENSION_DESCRIPTION
    "AI-powered tumor segmentation for clinical workflows")
set(EXTENSION_ICONURL
    "https://raw.githubusercontent.com/hkevin01/tumor-detection-segmentation/main/icon.png")
set(EXTENSION_SCREENSHOTURLS "")
# Specified as a space separated string, a list or 'NA' if any
set(EXTENSION_DEPENDS "NA")
set(EXTENSION_BUILD_SUBDIRECTORY inner-build)

set(SUPERBUILD_TOPLEVEL_PROJECT inner)

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(TumorSegmentationAI)

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})