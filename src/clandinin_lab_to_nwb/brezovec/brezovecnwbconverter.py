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
        metadata = self.get_metadata()
        session_start_time = metadata["NWBFile"]["session_start_time"]
        UTC_session_start_time = session_start_time.timestamp()
        for i in range(4):
            UTC_startig_time = metadata["Ophys"]["TwoPhotonSeries"][i]["starting_time"]
            aligned_starting_time = UTC_startig_time - UTC_session_start_time
            metadata["Ophys"]["TwoPhotonSeries"][i]["starting_time"] = aligned_starting_time
