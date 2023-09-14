"""Specialized extractor for reading TIFF files produced via ScanImage.

Classes
-------
ScanImageTiffImagingExtractor
    Specialized extractor for reading TIFF files produced via ScanImage.
"""
import logging
import re
from collections import Counter
from itertools import islice
from pathlib import Path
from types import ModuleType
from typing import Optional, Tuple, Union, List, Dict
from xml.etree import ElementTree

import numpy as np
from roiextractors.multiimagingextractor import MultiImagingExtractor
from roiextractors.imagingextractor import ImagingExtractor
from roiextractors.extraction_tools import PathType, get_package, DtypeType, ArrayType, FloatType
from neuroconv.utils import calculate_regular_series_rate


def _get_nifti_reader() -> ModuleType:
    return get_package(package_name="nibabel", installation_instructions="pip install nibabel")


def _determine_imaging_is_volumetric(folder_path: PathType) -> bool:
    """
    Determines whether imaging is volumetric based on 'zDevice' configuration value.
    The value is expected to be '1' for volumetric and '0' for single plane images.
    """
    xml_root = _parse_xml(folder_path=folder_path)
    z_device_element = xml_root.find(".//PVStateValue[@key='zDevice']")
    is_volumetric = bool(int(z_device_element.attrib["value"]))

    return is_volumetric


def _parse_xml(folder_path: PathType) -> ElementTree.Element:
    """
    Parses the XML configuration file into element tree and returns the root Element.
    """
    folder_path = Path(folder_path)
    xml_file_path = folder_path / f"{folder_path.name}.xml"
    assert xml_file_path.is_file(), f"The XML configuration file is not found at '{folder_path}'."
    tree = ElementTree.parse(xml_file_path)
    return tree.getroot()


class BrezovecMultiPlaneImagingExtractor(ImagingExtractor):
    """Specialized extractor Brezovec conversion project: reading NIfTI files produced by Bruker system."""

    extractor_name = "BrezovecMultiPlanImaging"
    is_writable = True
    mode = "folder"

    @classmethod
    def get_streams(cls, folder_path: PathType) -> dict:
        xml_root = _parse_xml(folder_path=folder_path)
        stream_name = [file.attrib for file in xml_root.findall(".//File")]
        streams = dict()
        streams["channel_streams"] = dict()
        for i in stream_name:
            streams["channel_streams"][i["channelName"]] = i["channel"]
            # I saved the channel id to retreive the stream name matching the .nii filename
        return streams

    def __init__(
        self,
        folder_path: PathType,
        stream_name: str,  # cannot be a optional argument because name does not match the file denomination
    ):
        """
        Create a BrezovecMultiPlaneImagingExtractor instance from a NIfTI file produced by Bruker system.

        Parameters
        ----------
        folder_path : PathType
            The path to the folder that contains the NIfTI image files (.ome.tif) and configuration files (.xml, .env).
        stream_name: str, optional
            The name of the recording channel (e.g. "Ch2").
        """
        self._niftifile = _get_nifti_reader()

        folder_path = Path(folder_path)
        nii_file_paths = list(folder_path.glob("*.nii"))
        assert nii_file_paths, f"The NIfTI image files are missing from '{folder_path}'."

        assert _determine_imaging_is_volumetric(folder_path=folder_path), (
            f"{self.extractor_name}Extractor is for volumetric imaging. "
            "For single imaging plane data use BrezovecSinglePlaneImagingExtractor."
        )

        self.folder_path = Path(folder_path)

        self._xml_root = _parse_xml(folder_path=folder_path)

        # TODO: All the checks on the channel_names, streams
        self.stream_name = stream_name
        streams = self.get_streams(folder_path=folder_path)
        self._channel_names = list(streams["channel_streams"].keys())
        assert (
            stream_name in self._channel_names
        ), f"The selected stream '{stream_name}' is not in the available channel stream '{self._channel_names}'!"

        file_names = list(folder_path.glob("*.nii"))
        # can't extract the names from xml --> they are listed as .ome.tif
        # TODO: to be implemented in a way that is not dependent to the filename

        channel_id = streams["channel_streams"][stream_name]
        file_for_stream = [file.as_posix() for file in file_names if "channel_" + channel_id in file.as_posix()]
        self.nibabel_image = self._niftifile.load(file_for_stream[0])

        self._num_rows = self.nibabel_image.shape[0]
        self._num_columns = self.nibabel_image.shape[1]
        self._num_planes_per_channel_stream = self.nibabel_image.shape[2]

        self._num_frames = self.nibabel_image.shape[-1]

        sampling_frequency = self.get_sampling_frequency()
        assert sampling_frequency is not None, "Could not determine the frame rate from the XML file."
        self._sampling_frequency = sampling_frequency

        self._times = None
        self.xml_metadata = self._get_xml_metadata()

    def get_image_size(self) -> Tuple[int, int, int]:
        return (self._num_rows, self._num_columns, self._num_planes_per_channel_stream)

    def get_num_frames(self) -> int:
        return self._num_frames

    def get_dtype(self) -> DtypeType:
        return self.nibabel_image.get_data_dtype()

    def get_sampling_frequency(self) -> float:
        """
        Determines the sampling rate from the difference in absolute timestamps of the first frame elements of each cycle or sequence element.
        """
        sampling_frequency = calculate_regular_series_rate(self.get_timestamps())
        return sampling_frequency

    def get_plane_acquisition_rate(self, cycle) -> float:
        """
        Determines the plane acquisition rate from the difference in absolute timestamps of frame elements in one cycle or sequence element.
        """
        timestamps = self.get_timestamps()
        plane_acquisition_rate = calculate_regular_series_rate(
            np.array(
                timestamps[
                    self._num_planes_per_channel_stream * (cycle - 1) : self._num_planes_per_channel_stream * cycle
                ]
            )
        )
        return plane_acquisition_rate

    def get_timestamps(self) -> np.ndarray:
        frame_elements = self._xml_root.findall(".//Frame")
        absolute_times = [float(frame.attrib["absoluteTime"]) for frame in frame_elements]
        timestamps = [absolute_times[t] for t in np.arange(0, len(absolute_times), self._num_planes_per_channel_stream)]
        return np.array(timestamps)

    def get_channel_names(self) -> list:
        return self._channel_names

    def get_num_channels(self) -> int:
        return len(self.get_channel_names())

    def get_video(
        self, start_frame: Optional[int] = None, end_frame: Optional[int] = None, channel: int = 0
    ) -> np.ndarray:
        if start_frame is not None and end_frame is not None and start_frame == end_frame:
            return self.nibabel_image.dataobj[:, :, :, start_frame]

        end_frame = end_frame or self.get_num_frames()
        start_frame = start_frame or 0

        return self.nibabel_image.dataobj[:, :, :, start_frame:end_frame].transpose(3, 0, 1, 2)

    def _get_xml_metadata(self) -> Dict[str, Union[str, List[Dict[str, str]]]]:
        """
        Parses the metadata in the root element that are under "PVStateValue" tag into
        a dictionary.
        """
        xml_metadata = dict()
        xml_metadata.update(**self._xml_root.attrib)
        for child in self._xml_root.findall(".//PVStateValue"):
            metadata_root_key = child.attrib["key"]
            if "value" in child.attrib:
                if metadata_root_key in xml_metadata:
                    continue
                xml_metadata[metadata_root_key] = child.attrib["value"]
            else:
                xml_metadata[metadata_root_key] = []
                for indexed_value in child:
                    if "description" in indexed_value.attrib:
                        xml_metadata[child.attrib["key"]].append(
                            {indexed_value.attrib["description"]: indexed_value.attrib["value"]}
                        )
                    elif "value" in indexed_value.attrib:
                        xml_metadata[child.attrib["key"]].append(
                            {indexed_value.attrib["index"]: indexed_value.attrib["value"]}
                        )
                    else:
                        for subindexed_value in indexed_value:
                            if "description" in subindexed_value.attrib:
                                xml_metadata[metadata_root_key].append(
                                    {subindexed_value.attrib["description"]: subindexed_value.attrib["value"]}
                                )
                            else:
                                xml_metadata[child.attrib["key"]].append(
                                    {indexed_value.attrib["index"]: subindexed_value.attrib["value"]}
                                )
        return xml_metadata


#
# TODO: different get_stream in the 3d and 2d case
# TODO: SinglePlaneExtractor
