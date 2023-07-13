"""Primary class for converting experiment-specific behavior."""
from pynwb.file import NWBFile

from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.utils import DeepDict

class BrezovecBehaviorInterface(BaseDataInterface):
    """Behavior interface for brezovec conversion"""

    keywords = ["fictrack", "visual tracking", "fictive path", "spherical treadmill", "visual fixation",]

    def __init__(self):
        # This should load the data lazily and prepare variables you need
        pass

    def get_metadata(self) -> DeepDict:
        # Automatically retrieve as much metadata as possible
        metadata = super().get_metadata()

        return metadata

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict):
        # All the custom code to write to PyNWB

        return nwbfile
