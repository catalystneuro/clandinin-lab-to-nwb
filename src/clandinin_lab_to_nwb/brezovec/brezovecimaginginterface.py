from dateutil.parser import parse
from clandinin_lab_to_nwb.brezovec.brezovecimagingextractor import BrezovecMultiPlaneImagingExtractor

from roiextractors import MultiImagingExtractor
from neuroconv.datainterfaces.ophys.baseimagingextractorinterface import BaseImagingExtractorInterface
from neuroconv.utils import FolderPathType
from neuroconv.utils.dict import DeepDict


class BrezovecMultiPlaneImagingInterface(BaseImagingExtractorInterface):
    """
    Data Interface for writing the Clandinin lab imaging data to NWB file using BrezovecMultiPlaneImagingExtractor.
    """

    Extractor = BrezovecMultiPlaneImagingExtractor

    def __init__(self, folder_path: FolderPathType, stream_name: str, verbose: bool = True):
        """
        Initialize reading of NIfTI files.

        Parameters
        ----------
        folder_path : FolderPathType
            The path to the folder that contains the NIfTI image files (.nii) and configuration files (.xml) from Bruker system.
        stream_name: str, optional
            The name of the recording channel.
        verbose : bool, default: True
        """
        super().__init__(
            folder_path=folder_path,
            stream_name=stream_name,
            verbose=verbose,
        )

    @classmethod
    def get_streams(cls, folder_path) -> dict:
        streams = BrezovecMultiPlaneImagingExtractor.get_streams(folder_path=folder_path)
        return streams

    def get_metadata(self) -> DeepDict:
        metadata = super().get_metadata()

        xml_metadata = self.imaging_extractor.xml_metadata
        session_start_time = parse(xml_metadata["date"])
        metadata["NWBFile"].update(session_start_time=session_start_time)

        description = f"Version {xml_metadata['version']}"
        device_name = "BrukerFluorescenceMicroscope"  # TODO doucle check in the paper
        metadata["Ophys"]["Device"][0].update(
            name=device_name,
            description=description,
        )

        imaging_plane_metadata = metadata["Ophys"]["ImagingPlane"][0]
        imaging_plane_metadata.update(
            device=device_name,
            imaging_rate=self.imaging_extractor.get_sampling_frequency(),
        )
        two_photon_series_metadata = metadata["Ophys"]["TwoPhotonSeries"][0]
        two_photon_series_metadata.update(
            description="Imaging data acquired from the Bruker Two-Photon Microscope and transform to NIfTI.",  # TODO doucle check in the paper
            unit="px",
            format=".nii",
            scan_line_rate=1 / float(xml_metadata["scanLinePeriod"]),
        )

        microns_per_pixel = xml_metadata["micronsPerPixel"]
        if microns_per_pixel:
            image_size_in_pixels = self.imaging_extractor.get_image_size()
            x_position_in_meters = float(microns_per_pixel[0]["XAxis"]) / 1e6
            y_position_in_meters = float(microns_per_pixel[1]["YAxis"]) / 1e6
            z_plane_position_in_meters = float(microns_per_pixel[2]["ZAxis"]) / 1e6
            grid_spacing = [
                y_position_in_meters,
                x_position_in_meters,
            ]

            imaging_plane_metadata.update(
                grid_spacing=grid_spacing, description=f"The plane imaged at {z_plane_position_in_meters} meters depth."
            )

            field_of_view = [
                y_position_in_meters * image_size_in_pixels[1],
                x_position_in_meters * image_size_in_pixels[0],
                z_plane_position_in_meters,
            ]
            two_photon_series_metadata.update(field_of_view=field_of_view)

        return metadata
