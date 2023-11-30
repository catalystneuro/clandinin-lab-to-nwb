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
        fictrac_interface = self.data_interface_objects["FicTrac"]
        video_interface = self.data_interface_objects["Video"]
        functional_green_interface = self.data_interface_objects["ImagingFunctionalGreen"]
        functional_red_interface = self.data_interface_objects["ImagingFunctionalRed"]
        anatomical_green_interface = self.data_interface_objects["ImagingAnatomicalGreen"]
        anatomical_red_interface = self.data_interface_objects["ImagingAnatomicalRed"]

        # As the authors we create a timestamps for the FicTrac as if they have uniform sampling rate
        sampling_rate = 50  # Hz
        num_samples = fictrac_interface.get_original_timestamps().size
        duration = num_samples / sampling_rate

        unifom_timestamps = np.linspace(0, duration, num_samples, endpoint=False)

        fictrac_interface.set_aligned_timestamps(unifom_timestamps)
        video_interface.set_aligned_timestamps([unifom_timestamps])

        # The functional imaging is already aligned but we need to shift the anatomical imaging
        # Note that both channels start at the same time
        functional_datetime = functional_green_interface.get_series_datetime()
        functional_timestamp = functional_datetime.timestamp()

        anatomy_datetime = anatomical_green_interface.get_series_datetime()
        anatomy_timestamp = anatomy_datetime.timestamp()
        aligned_starting_time = anatomy_timestamp - functional_timestamp
        anatomical_green_interface.set_aligned_starting_time(aligned_starting_time)
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
