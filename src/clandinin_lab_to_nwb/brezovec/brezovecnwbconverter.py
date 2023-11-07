"""Primary NWBConverter class for this dataset."""
from typing import Optional
from neuroconv.utils.dict import DeepDict
from datetime import datetime
from zoneinfo import ZoneInfo

from pynwb import NWBFile

from neuroconv import NWBConverter
from neuroconv.datainterfaces import (
    FicTracDataInterface,
    VideoInterface,
)
from .brezovecimaginginterface import BrezovecImagingInterface


def read_session_start_time_from_file(xml_file):
    from xml.etree import ElementTree
    from dateutil import parser

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


class BrezovecNWBConverter(NWBConverter):
    """Primary conversion class for the brezovec conversion project."""

    data_interface_classes = dict(
        FicTrac=FicTracDataInterface,
        ImagingFunctionalGreen=BrezovecImagingInterface,
        ImagingFunctionalRed=BrezovecImagingInterface,
        ImagingAnatomicalGreen=BrezovecImagingInterface,
        ImagingAnatomicalRed=BrezovecImagingInterface,
        Video=VideoInterface,
    )

    def temporally_align_data_interfaces(self):
        functional_green_interface = self.data_interface_objects["ImagingFunctionalGreen"]
        functional_red_interface = self.data_interface_objects["ImagingFunctionalRed"]
        anatomical_green_interface = self.data_interface_objects["ImagingAnatomicalGreen"]
        anatomical_red_interface = self.data_interface_objects["ImagingAnatomicalRed"]

        session_start_time = functional_green_interface.imaging_extractor.get_series_datetime()
        UTC_session_start_time = session_start_time.timestamp()
        aligned_starting_time = 0.0
        functional_green_interface.set_aligned_starting_time(aligned_starting_time)

        series_start_time = functional_red_interface.imaging_extractor.get_series_datetime()
        UTC_series_start_time = series_start_time.timestamp()
        aligned_starting_time = UTC_series_start_time - UTC_session_start_time
        functional_red_interface.set_aligned_starting_time(aligned_starting_time)

        series_start_time = anatomical_green_interface.imaging_extractor.get_series_datetime()
        UTC_series_start_time = series_start_time.timestamp()
        aligned_starting_time = UTC_series_start_time - UTC_session_start_time
        anatomical_green_interface.set_aligned_starting_time(aligned_starting_time)

        series_start_time = anatomical_red_interface.imaging_extractor.get_series_datetime()
        UTC_series_start_time = series_start_time.timestamp()
        aligned_starting_time = UTC_series_start_time - UTC_session_start_time
        anatomical_red_interface.set_aligned_starting_time(aligned_starting_time)

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata, conversion_options: Optional[dict] = None) -> None:
        super().add_to_nwbfile(nwbfile, metadata, conversion_options=conversion_options)

        # Add the camera
        from pynwb.device import Device

        name = "Flea FL3-U3-13E4M-C"
        description = (
            "Sensor used for imaging with FicTrac at 50 Hz with Edmund Optics 100 mm C Series Fixed Focal Length Lens"
        )
        manufacturer = "Teledyne FLIR Systems, Inc."
        camera_device = Device(name, description=description, manufacturer=manufacturer)

        nwbfile.add_device(camera_device)
