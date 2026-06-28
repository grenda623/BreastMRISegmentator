cmake_minimum_required(VERSION 3.16.3)

project(SlicerBreastMRISegmentator)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "https://github.com/grenda623/SlicerBreastMRISegmentator")
set(EXTENSION_CATEGORY "Segmentation")
set(EXTENSION_CONTRIBUTORS "Renda Guo (KTH), Rodrigo Moreno (KTH)")
set(EXTENSION_DESCRIPTION "Fully automatic AI segmentation of breast, fibroglandular tissue (FGT) and tumor on DCE-MRI, based on the BreastMRISegmentator nnU-Net model (Exp4x, 4-channel kinetic input).")
set(EXTENSION_ICONURL "https://github.com/grenda623/SlicerBreastMRISegmentator/raw/main/BreastMRISegmentator/Resources/Icons/BreastMRISegmentator_full_icon.png")
set(EXTENSION_SCREENSHOTURLS "https://github.com/grenda623/SlicerBreastMRISegmentator/raw/main/Screenshots/1.png")
# Unlike DentalSegmentator, we do NOT depend on the "NNUNet" Slicer extension:
# inference is delegated to the pip-installed `breast-mri-segmentator` package,
# which builds the 4-channel kinetic input and runs nnUNetv2_predict itself.
set(EXTENSION_DEPENDS "NA")

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(BreastMRISegmentator)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
