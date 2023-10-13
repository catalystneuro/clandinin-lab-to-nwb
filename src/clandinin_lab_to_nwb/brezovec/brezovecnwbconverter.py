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
