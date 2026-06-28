"""Slicer-runtime tests for the BreastMRISegmentator extension.

These run inside 3D Slicer (via SlicerPythonTestRunner / pytest), NOT in the
parent repo's lightweight CI — they need the Slicer Python environment and, for
the end-to-end case, a GPU + the Exp4x weights.
"""
