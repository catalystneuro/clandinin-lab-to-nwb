"""Primary NWBConverter class for this dataset."""
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
