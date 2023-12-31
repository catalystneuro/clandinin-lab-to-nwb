from dateutil.parser import parse
from clandinin_lab_to_nwb.brezovec.brezovecimagingextractor import (
    BrezovecMultiPlaneImagingExtractor,
    NIfTIImagingExtractor,
)
from pathlib import Path
from datetime import datetime

import numpy as np

from neuroconv.datainterfaces.ophys.baseimagingextractorinterface import BaseImagingExtractorInterface
from neuroconv.utils import FolderPathType, FilePathType
from neuroconv.utils.dict import DeepDict
from typing import Literal


class NiftiImagingInterface(BaseImagingExtractorInterface):
    Extractor = NIfTIImagingExtractor

    def __init__(
        self,
        file_path: FilePathType,
        verbose: bool = True,
    ):
        super().__init__(
            file_path=file_path,
            verbose=verbose,
        )

    def get_metadata(self):
        metadata = super().get_metadata()

        nibabel_image = self.imaging_extractor.nibabel_image
        header = nibabel_image.header
        voxel_sizes = header.get_zooms()
        width, height, depth = self.imaging_extractor.get_image_size()
        num_frames = self.imaging_extractor.get_num_frames()

        units = header.get_xyzt_units()
        origin_coords_unit = units[0]
        grid_spacing_unit = units[0]

        affine_matrix = header.get_qform()
        # Get diagonal of affine matrix
        grid_spacing = np.diag(affine_matrix[:3, :3])[:]
        origin_coords = affine_matrix[:3, 3]

        # specific for this project

        indicator = "GCaMP6f"
        optical_channel_metadata = {
            "name": "Green",
            "emission_lambda": 513.0,
            "description": "Green channel of the microscope, 525/50 nm filter.",
        }

        version = "5.5.64.100"  # Taken from the XML file
        device_name = "BrukerFluorescenceMicroscope"
        metadata["Ophys"]["Device"][0].update(
            name=device_name, description=f"Bruker Ultima IV, Version {version}", manufacturer="Bruker"
        )

        imaging_plane_name = f"ImagingPlaneFunctionalGreenProcessed"
        imaging_plane_metadata = metadata["Ophys"]["ImagingPlane"][0]
        imaging_plane_metadata.update(
            name=imaging_plane_name,
            optical_channel=[optical_channel_metadata],
            device=device_name,
            excitation_lambda=920.0,  #   Chameleon Vision II femtosecond laser (Coherent) at 920 nm.
            indicator=indicator,
            grid_spacing=grid_spacing,
            grid_spacing_unit=grid_spacing_unit,
            origin_coords=origin_coords,
            origin_coords_unit=origin_coords_unit,
            location="whole brain",
        )

        description = "motion corrected high-pass temporal filtered z-scored and registered into a common space, the Functional Drosophila Atlas"

        two_photon_series_metadata = metadata["Ophys"]["TwoPhotonSeries"][0]
        two_photon_series_metadata.update(
            name=f"TwoPhotonSeriesFunctionalGreenProcessed",
            imaging_plane=imaging_plane_name,
            description=description,
            unit="n.a.",
        )

        return metadata


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
        self.folder_path = folder_path

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
        version = xml_metadata["version"]
        metadata["Ophys"]["Device"][0].update(
            name=device_name, description=f"Bruker Ultima IV, Version {version}", manufacturer="Bruker"
        )

        indicator = indicators[self.channel]
        imaging_plane_name = f"ImagingPlane{indicator}{self.imaging_purpose}"
        imaging_plane_metadata = metadata["Ophys"]["ImagingPlane"][0]
        imaging_plane_metadata.update(
            name=imaging_plane_name,
            optical_channel=[optical_channel_metadata],
            device=device_name,
            excitation_lambda=920.0,  #   Chameleon Vision II femtosecond laser (Coherent) at 920 nm.
            indicator=indicator,
            imaging_rate=self.imaging_extractor.get_sampling_frequency(),
            location="whole brain",
        )

        two_photon_series_metadata = metadata["Ophys"]["TwoPhotonSeries"][0]
        two_photon_series_metadata.update(
            name=f"TwoPhotonSeries{self.imaging_purpose}{self.channel}",
            imaging_plane=imaging_plane_name,
            scan_line_rate=1 / float(xml_metadata["scanLinePeriod"]),
            rate=self.imaging_extractor.get_sampling_frequency(),
            description=f"{self.imaging_purpose} imaging data ({indicator})",
            unit="n.a.",
        )

        microns_per_pixel = xml_metadata["micronsPerPixel"]
        if microns_per_pixel:
            pixel_size_in_meters_x = float(microns_per_pixel[0]["XAxis"]) / 1e6
            pixel_size_in_meters_y = float(microns_per_pixel[1]["YAxis"]) / 1e6
            pixel_size_in_meters_z = float(microns_per_pixel[2]["ZAxis"]) / 1e6
            grid_spacing = [pixel_size_in_meters_y, pixel_size_in_meters_x, pixel_size_in_meters_z]

            imaging_plane_metadata.update(grid_spacing=grid_spacing, grid_spacing_unit="meters")

            image_size_in_pixels = self.imaging_extractor.get_image_size()

            field_of_view = [
                pixel_size_in_meters_y * image_size_in_pixels[1],
                pixel_size_in_meters_x * image_size_in_pixels[0],
                pixel_size_in_meters_z * image_size_in_pixels[2],
            ]

            two_photon_series_metadata.update(
                field_of_view=field_of_view, dimension=image_size_in_pixels, resolution=pixel_size_in_meters_x
            )

        return metadata

    two_photon_series_index = {
        "TwoPhotonSeriesFunctionalGreen": 0,
        "TwoPhotonSeriesFunctionalRed": 1,
        "TwoPhotonSeriesAnatomicalGreen": 2,
        "TwoPhotonSeriesAnatomicalRed": 3,
    }

    def get_series_datetime(self):
        folder_path = Path(self.folder_path)
        xml_file_path = folder_path / f"{folder_path.name}.xml"
        assert xml_file_path.is_file(), f"The XML configuration file is not found at '{folder_path}'."

        series_datetime = self.read_session_start_time_from_file(xml_file_path)
        return series_datetime

    @staticmethod
    def read_session_start_time_from_file(xml_file_path):
        from xml.etree import ElementTree
        from dateutil import parser

        date = None
        first_timestamp = None

        for event, elem in ElementTree.iterparse(xml_file_path, events=("start", "end")):
            # Extract the date from PVScan
            if date is None and elem.tag == "PVScan" and event == "end":
                date_string = elem.attrib.get("date")
                date = datetime.strptime(date_string, "%m/%d/%Y %I:%M:%S %p")
                elem.clear()

            # Extract the time from Sequence
            if first_timestamp is None and elem.tag == "Sequence" and event == "end":
                sequence_time = elem.get("time")
                first_timestamp = parser.parse(sequence_time)
                elem.clear()

            if date is not None and first_timestamp is not None:
                break

        combined_datetime = datetime(
            date.year,
            date.month,
            date.day,
            first_timestamp.hour,
            first_timestamp.minute,
            first_timestamp.second,
            first_timestamp.microsecond,
        )

        return combined_datetime
