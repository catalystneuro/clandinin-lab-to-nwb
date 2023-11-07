from pathlib import Path
from types import ModuleType
from typing import Optional, Tuple, Union, List, Dict
from xml.etree import ElementTree
from dateutil import parser

import numpy as np
from roiextractors.imagingextractor import ImagingExtractor
from roiextractors.extraction_tools import PathType, get_package, DtypeType
from neuroconv.utils import calculate_regular_series_rate
from datetime import datetime


def _get_nifti_reader() -> ModuleType:
    return get_package(package_name="nibabel", installation_instructions="pip install nibabel")


def get_channels_from_first_frame(xml_file):
    """
    Extract channel and channelName attributes from the File tags within the first Frame tag.

    Parameters
    ----------
    xml_file : str or Path
        Path to the XML file.

    Returns
    -------
    list of tuple
        A list containing tuples. Each tuple consists of (channel, channelName) attributes.
    """

    file_attributes_list = []
    for event, elem in ElementTree.iterparse(xml_file, events=("start", "end")):
        # We only need one frame so get out out of the loop when the first Frame tag is closed
        if elem.tag == "Frame" and event == "end":
            break

        # For every file we extract the channel and channelName attributes and then clear the element
        if elem.tag == "File" and event == "end":
            file_attributes_list.append((elem.attrib.get("channel"), elem.attrib.get("channelName")))
            elem.clear()

    return file_attributes_list


def read_session_date_from_file(folder_path: PathType):
    from xml.etree import ElementTree

    folder_path = Path(folder_path)
    xml_file = folder_path / f"{folder_path.name}.xml"
    assert xml_file.is_file(), f"The XML configuration file is not found at '{folder_path}'."

    date = None
    first_timestamp = None
    for event, elem in ElementTree.iterparse(xml_file, events=("start", "end")):
        # Extract the date from PVScan
        if date is None and elem.tag == "PVScan" and event == "end":
            date_string = elem.attrib.get("date")
            date = datetime.strptime(date_string, "%m/%d/%Y %H:%M:%S  %p")
            elem.clear()

        # Extract the time from Sequence
        if first_timestamp is None and elem.tag == "Sequence" and event == "end":
            sequence_time = elem.get("time")
            first_timestamp = parser.parse(sequence_time)
            elem.clear()

        if date is not None and first_timestamp is not None:
            break

    combined_datetime = datetime(
        date.year,
        date.month,
        date.day,
        first_timestamp.hour,
        first_timestamp.minute,
        first_timestamp.second,
        first_timestamp.microsecond,
    )

    return combined_datetime


def _parse_xml(folder_path: PathType) -> ElementTree.Element:
    """
    Parses the XML configuration file into element tree and returns the root Element.
    """
    folder_path = Path(folder_path)
    xml_file_path = folder_path / f"{folder_path.name}.xml"
    assert xml_file_path.is_file(), f"The XML configuration file is not found at '{folder_path}'."
    tree = ElementTree.parse(xml_file_path)
    return tree.getroot()


def _get_xml_file_path(folder_path: PathType) -> Path:
    folder_path = Path(folder_path)
    xml_file_path = folder_path / f"{folder_path.name}.xml"
    assert xml_file_path.is_file(), f"The XML configuration file is not found at '{folder_path}'."
    return xml_file_path


class NIfTIImagingExtractor(ImagingExtractor):
    def __init__(
        self, file_path: PathType, sampling_frequency: Optional[float] = None, channel_name: Optional[str] = None
    ):
        self._niftifile = _get_nifti_reader()
        self.nibabel_image = self._niftifile.load(file_path)
        self._num_rows = self.nibabel_image.shape[1]
        self._num_columns = self.nibabel_image.shape[0]
        self._num_planes = self.nibabel_image.shape[2]
        self._num_frames = self.nibabel_image.shape[-1]
        self._sampling_frequency = sampling_frequency
        self._times = None
        self.channel_name = channel_name if channel_name is not None else "no_name"

    def get_video(
        self, start_frame: Optional[int] = None, end_frame: Optional[int] = None, channel: int = 0
    ) -> np.ndarray:
        """
        The nifti format is:
        (x - columns - width, y - rows - heigth, z, t)
        which we transform to the roiextractors convention:
        (t, y - rows, x - columns, z)
        """
        if start_frame is not None and end_frame is not None and start_frame == end_frame:
            return self.nibabel_image.dataobj[:, :, :, start_frame].transpose(1, 0, 2)

        end_frame = end_frame or self.get_num_frames()
        start_frame = start_frame or 0

        return self.nibabel_image.dataobj[:, :, :, start_frame:end_frame].transpose(3, 1, 0, 2)

    def get_image_size(self) -> Tuple[int, int, int]:
        return (self._num_rows, self._num_columns, self._num_planes)

    def get_num_frames(self) -> int:
        return self._num_frames

    def get_dtype(self) -> DtypeType:
        return self.nibabel_image.get_data_dtype()

    def get_sampling_frequency(self) -> float:
        return self._sampling_frequency

    # Since we define one TwoPhotonSeries per channel, here it should return the name of the single channel
    def get_channel_names(self) -> list:
        # return self._channel_names
        return [self.channel_name]

    def get_num_channels(self) -> int:
        return 1  # len(self.get_channel_names())


class BrezovecMultiPlaneImagingExtractor(NIfTIImagingExtractor):
    """Specialized extractor Brezovec conversion project: reading NIfTI files based on data produced by Bruker system."""

    extractor_name = "BrezovecMultiPlaneImaging"
    is_writable = True
    mode = "folder"

    @classmethod
    def get_streams(cls, folder_path: PathType) -> dict:
        xml_file_path = _get_xml_file_path(folder_path)
        channel_info = get_channels_from_first_frame(xml_file_path)
        channel_info_formated = {f"{channel_name}": f"{channel}" for channel, channel_name in channel_info}
        streams = {"channel_streams": channel_info_formated}

        return streams

    @classmethod
    def _determine_imaging_is_volumetric(cls, xml_root: ElementTree.Element) -> bool:
        """
        Determines whether imaging is volumetric based on 'zDevice' configuration value.
        The value is expected to be '1' for volumetric and '0' for single plane images.
        """
        z_device_element = xml_root.find(".//PVStateValue[@key='zDevice']")
        is_volumetric = bool(int(z_device_element.attrib["value"]))

        return is_volumetric

    def __init__(
        self,
        folder_path: PathType,
        stream_name: str,
    ):
        """
        Create a BrezovecMultiPlaneImagingExtractor instance from a NIfTI file produced by Bruker system.

        Parameters
        ----------
        folder_path : PathType
            The path to the folder that contains the NIfTI image files (.nii) and configuration files (.xml).
        stream_name: str, optional
            The name of the recording channel.
        """
        self._niftifile = _get_nifti_reader()

        folder_path = Path(folder_path)
        nii_file_paths = list(folder_path.glob("*.nii"))
        assert nii_file_paths, f"The NIfTI image files are missing from '{folder_path}'."

        self.folder_path = Path(folder_path)

        self._xml_root = _parse_xml(folder_path=folder_path)

        assert self._determine_imaging_is_volumetric(self._xml_root), (
            f"{self.extractor_name}Extractor is for volumetric imaging. "
            "For single imaging plane data use BrezovecSinglePlaneImagingExtractor."
        )

        self.stream_name = stream_name
        streams = self.get_streams(folder_path=folder_path)
        self._channel_names = list(streams["channel_streams"].keys())
        assert (
            stream_name in self._channel_names
        ), f"The selected stream '{stream_name}' is not in the available channel stream '{self._channel_names}'!"

        nifti_files_in_folder = list(folder_path.glob("*.nii"))

        channel_id = streams["channel_streams"][stream_name]
        file_path = next((path for path in nifti_files_in_folder if "channel_" + channel_id in path.name), None)
        if file_path is None:
            raise FileNotFoundError(f"Could not find file {file_path} for stream '{stream_name}'!")

        # Sampling frequency is calculate from `calculate_regular_series_rate` which in turn
        # Requires num_planes which requires initialization of the parent class to get the nifti_image
        # TODO: Decouple the `calculate_regular_series_rate` from the `num_planes` attribute.
        super().__init__(file_path, sampling_frequency=None, channel_name=stream_name)

        sampling_frequency = calculate_regular_series_rate(self.get_timestamps())
        assert sampling_frequency is not None, "Could not determine the frame rate from the XML file."
        self._sampling_frequency = sampling_frequency

        self._times = None
        self.xml_metadata = self._get_xml_metadata()

    def get_plane_acquisition_rate(self, cycle) -> float:
        """
        Determines the plane acquisition rate from the difference in absolute timestamps of frame elements in one cycle or sequence element.
        """
        timestamps = self.get_timestamps()
        plane_acquisition_rate = calculate_regular_series_rate(
            np.array(timestamps[self._num_planes * (cycle - 1) : self._num_planes * cycle])
        )
        return plane_acquisition_rate

    def get_timestamps(self) -> np.ndarray:
        frame_elements = self._xml_root.findall(".//Frame")
        absolute_times = [
            float(frame.attrib["absoluteTime"]) for frame in frame_elements
        ]  # TODO should we use absoluteTime or relativeTime?
        timestamps = [absolute_times[t] for t in np.arange(0, len(absolute_times), self._num_planes)]
        return np.array(timestamps)

    def get_series_datetime(self):
        series_datetime = read_session_date_from_file(folder_path=self.folder_path)
        return series_datetime

    # Since we define one TwoPhotonSeries per channel, here it should return the name of the single channel
    def get_channel_names(self) -> list:
        # return self._channel_names
        return [self.stream_name]

    def get_num_channels(self) -> int:
        return 1  # len(self.get_channel_names())

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
