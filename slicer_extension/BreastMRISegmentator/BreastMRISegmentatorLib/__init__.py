"""BreastMRISegmentator Slicer extension library.

Public surface mirrors gaudot/SlicerDentalSegmentator's ``DentalSegmentatorLib``.
"""
from .Signal import Signal
from .SegmentationWidget import SegmentationWidget, SegmentationLogic

__all__ = ["Signal", "SegmentationWidget", "SegmentationLogic"]
