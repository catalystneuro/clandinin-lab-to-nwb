"""Primary NWBConverter class for this dataset."""
from typing import Optional
from pathlib import Path
from neuroconv.utils.dict import DeepDict
from zoneinfo import ZoneInfo
import numpy as np

from pynwb import NWBFile

from neuroconv import NWBConverter
from neuroconv.datainterfaces import (
    FicTracDataInterface,
    VideoInterface,
)
from .brezovecimaginginterface import BrezovecImagingInterface


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

    def get_metadata(self) -> DeepDict:
        metadata = super().get_metadata()

        # Add datetime to conversion from the Functional Green imaging data
        folder_path = self.data_interface_objects["ImagingFunctionalGreen"].folder_path
        xml_file_path = Path(folder_path) / f"{Path(folder_path).name}.xml"

        functional_imaging_datetime = BrezovecImagingInterface.read_session_start_time_from_file(xml_file_path)
        timezone = ZoneInfo("America/Los_Angeles")  # Time zone for Stanford, California
        session_start_time = functional_imaging_datetime.replace(tzinfo=timezone)
        metadata["NWBFile"]["session_start_time"] = session_start_time

        return super().get_metadata()

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
