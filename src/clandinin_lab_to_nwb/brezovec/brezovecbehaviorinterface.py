"""Primary class for converting experiment-specific behavior."""
from pynwb.file import NWBFile

from neuroconv.basedatainterface import BaseDataInterface

class BrezovecBehaviorInterface(BaseDataInterface):
    """Behavior interface for brezovec conversion"""

    def __init__(self):
        # This should load the data lazily and prepare variables you need
        pass

    def get_metadata(self):
        # Automatically retrieve as much metadata as possible
        metadata = super().get_metadata()

        return metadata

    def add_to_nwb(self, nwbfile: NWBFile, metadata: dict):
        # All the custom code to write to PyNWB

        return nwbfile
