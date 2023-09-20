"""Primary NWBConverter class for this dataset."""
from neuroconv import NWBConverter
from neuroconv.datainterfaces import (
    FicTracDataInterface,
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
        # FicTrac=FicTracDataInterface,
        OphysGreenFun=BrezovecFunctionalGreenImagingInterface,
        OphysRedFun=BrezovecFunctionalRedImagingInterface,
        OphysGreenAna=BrezovecAnatomicalGreenImagingInterface,
        OphysRedAna=BrezovecAnatomicalRedImagingInterface,
    )
