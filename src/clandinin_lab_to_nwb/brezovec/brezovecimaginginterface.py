"""Specialized extractor for reading TIFF files produced via ScanImage.

Classes
-------
ScanImageTiffImagingExtractor
    Specialized extractor for reading TIFF files produced via ScanImage.
"""
from pathlib import Path
from typing import Optional, Tuple
from warnings import warn

import numpy as np

from roiextractors.extraction_tools import PathType, FloatType, DtypeType, ArrayType, get_package
from roiextractors.imagingextractor import ImagingExtractor

import nibabel as nib


class BrezovecImagingExtractor(ImagingExtractor):
    """Specialized extractor for reading TIFF files produced via ScanImage."""

    extractor_name = "ScanImageTiffImaging"
    is_writable = True
    mode = "file"

    def __init__(
        self,
        file_path: PathType,
        sampling_frequency: FloatType,
    ):
        """Create a BrezovecImagingExtractor instance from a niff file produced by ScanImage.
        .

                Parameters
                ----------
                file_path : PathType
                    Path to the nii file.
                sampling_frequency : float
                    The frequency at which the frames were sampled, in Hz.
        """

        super().__init__()
        self.file_path = Path(file_path)
        self._sampling_frequency = sampling_frequency
        valid_suffixes = [".nii"]
        file_path_suffix_is_valid = self.file_path.suffix in valid_suffixes
        assert file_path_suffix_is_valid, f"The {file_path.suffix} should be .nii"

        # For the brezovec data and reading the paper it seems that the img.shape
        # is x, y, z,  time.

    def get_image_size(self) -> Tuple[int, int]:

        img = nib.load(self.file_path)
        self._num_rows = img.shape[0]  # TODO: Check, confirm rows x? or y?
        self._num_columns = img.shape[1]
        return (self._num_rows, self._num_columns)

    def get_num_frames(self) -> int:
        img = nib.load(self.file_path)
        self._num_frames = img.shape[-1]
        return self._num_frames

    def get_dtype(self) -> DtypeType:
        img = nib.load(self.file_path)
        return img.get_data_dtype()

    def get_sampling_frequency(self) -> float:
        return self._sampling_frequency

    def get_channel_names(self) -> list:
        # What should be the channel names here?
        self._channel_names = ["channel"]
        return self._channel_names

    def get_num_channels(self) -> int:
        return len(self.get_channel_names())

    def get_video(self, start_frame=None, end_frame=None) -> np.ndarray:
        img = nib.load(self.file_path)
        # get_fdata could be
        # Or img.dataobj
        # TODO: One of them is lazy, remember which, read nibabel documentation for best pratices

        return img.dataobj[:, :, :, start_frame:end_frame]
