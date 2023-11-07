from dateutil.parser import parse
from clandinin_lab_to_nwb.brezovec.brezovecimagingextractor import BrezovecMultiPlaneImagingExtractor

from neuroconv.datainterfaces.ophys.baseimagingextractorinterface import BaseImagingExtractorInterface
from neuroconv.utils import FolderPathType
from neuroconv.utils.dict import DeepDict
from typing import Literal


class BrezovecImagingInterface(BaseImagingExtractorInterface):
    """
    Data Interface for writing imaging data for the Clandinin lab to NWB file using BrezovecMultiPlaneImagingExtractor.
    """

    Extractor = BrezovecMultiPlaneImagingExtractor

    def __init__(
        self,
        folder_path: FolderPathType,
        channel: Literal["Red", "Green"],
        imaging_purpose: Literal["Functional", "Anatomical"],
        verbose: bool = True,
    ):
        super().__init__(
            folder_path=folder_path,
            stream_name=channel,
            verbose=verbose,
        )
        self.channel = channel
        self.imaging_purpose = imaging_purpose

    @classmethod
    def get_streams(cls, folder_path) -> dict:
        streams = cls.Extractor.get_streams(folder_path=folder_path)
        return streams

    def get_metadata(self) -> DeepDict:
        metadata = super().get_metadata()
        xml_metadata = self.imaging_extractor.xml_metadata

        indicators = dict(Red="tdTomato", Green="GCaMP6f")

        # Configure metadata according to the channel (Green/Red) and imaging_purpose (Functional/Anatomical)
        channel_metadata = {
            "Green": {
                "name": "Green",
                "emission_lambda": 513.0,
                "description": "Green channel of the microscope, 525/50 nm filter.",
            },
            "Red": {
                "name": "Red",
                "emission_lambda": 581.0,
                "description": "Red channel of the microscope, 550/50 nm filter.",
            },
        }[self.channel]

        optical_channel_metadata = channel_metadata

        device_name = "BrukerFluorescenceMicroscope"
        metadata["Ophys"]["Device"][0].update(
            name=device_name, description=f"Bruker Ultima IV, Version {xml_metadata['version']}", manufacturer="Bruker"
        )

        indicator = indicators[self.channel]
        imaging_plane_name = f"ImagingPlane{indicator}{self.imaging_purpose}"
        imaging_plane_metadata = metadata["Ophys"]["ImagingPlane"][0]
        imaging_plane_metadata.update(
            name=imaging_plane_name,
            optical_channel=[optical_channel_metadata],
            device=device_name,
            excitation_lambda=920.0,
            indicator=indicator,
            imaging_rate=self.imaging_extractor.get_sampling_frequency(),
        )

        two_photon_series_metadata = metadata["Ophys"]["TwoPhotonSeries"][0]
        two_photon_series_metadata.update(
            name=f"TwoPhotonSeries{self.imaging_purpose}{self.channel}",
            imaging_plane=imaging_plane_name,
            scan_line_rate=1 / float(xml_metadata["scanLinePeriod"]),
            rate=self.imaging_extractor.get_sampling_frequency(),
            description=f"{self.imaging_purpose} imaging data ({indicator}) acquired from the Bruker Two-Photon Microscope",
            unit="px",
        )

        microns_per_pixel = xml_metadata["micronsPerPixel"]
        if microns_per_pixel:
            image_size_in_pixels = self.imaging_extractor.get_image_size()
            x_position_in_meters = float(microns_per_pixel[0]["XAxis"]) / 1e6
            y_position_in_meters = float(microns_per_pixel[1]["YAxis"]) / 1e6
            z_plane_position_in_meters = float(microns_per_pixel[2]["ZAxis"]) / 1e6
            grid_spacing = [y_position_in_meters, x_position_in_meters, z_plane_position_in_meters]

            imaging_plane_metadata.update(grid_spacing=grid_spacing)

            field_of_view = [
                y_position_in_meters * image_size_in_pixels[1],
                x_position_in_meters * image_size_in_pixels[0],
                z_plane_position_in_meters * image_size_in_pixels[2],
            ]

            two_photon_series_metadata.update(
                field_of_view=field_of_view, dimension=image_size_in_pixels, resolution=x_position_in_meters
            )

        return metadata

    two_photon_series_index = {
        "TwoPhotonSeriesFunctionalGreen": 0,
        "TwoPhotonSeriesFunctionalRed": 1,
        "TwoPhotonSeriesAnatomicalGreen": 2,
        "TwoPhotonSeriesAnatomicalRed": 3,
    }
