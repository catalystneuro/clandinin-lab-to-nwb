"""Primary NWBConverter class for this dataset."""
from typing import Dict, List, Optional, Union

from pynwb import NWBFile

from neuroconv import NWBConverter
from neuroconv.datainterfaces import (
    FicTracDataInterface,
    VideoInterface,
)
from .brezovecimaginginterface import (
    BrezovecFunctionalGreenImagingInterface,
    BrezovecFunctionalRedImagingInterface,
    BrezovecAnatomicalGreenImagingInterface,
    BrezovecAnatomicalRedImagingInterface,
)


class BrezovecNWBConverter(NWBConverter):
    """Primary conversion class for the brezovec conversion project."""

    data_interface_classes = dict(
        FicTrac=FicTracDataInterface,
        ImagingFunctionalGreen=BrezovecFunctionalGreenImagingInterface,
        ImagingFunctionalRed=BrezovecFunctionalRedImagingInterface,
        ImagingAnatomicalGreen=BrezovecAnatomicalGreenImagingInterface,
        ImagingAnatomicalRed=BrezovecAnatomicalRedImagingInterface,
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
        description = "Sensor used for imaging at 50 Hz with Edmund Optics 100 mm C Series Fixed Focal Length Lens"
        manufacturer = "Teledyne FLIR Systems, Inc."
        camera_device = Device(name, description=description, manufacturer=manufacturer)

        nwbfile.add_device(camera_device)
