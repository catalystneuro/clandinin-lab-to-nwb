from dateutil.parser import parse
from clandinin_lab_to_nwb.brezovec.brezovecimagingextractor import BrezovecMultiPlaneImagingExtractor

from neuroconv.datainterfaces.ophys.baseimagingextractorinterface import BaseImagingExtractorInterface
from neuroconv.utils import FolderPathType
from neuroconv.utils.dict import DeepDict


class BrezovecFunctionalGreenImagingInterface(BaseImagingExtractorInterface):
    """
    Data Interface for writing the functional imaging data (GCaMP6f) for Clandinin lab to NWB file using BrezovecMultiPlaneImagingExtractor.
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

        # channel_name = 'Green'
        # metadata["Ophys"]["OpticalChannel"][0].update(
        #     name=channel_name,
        #     emission_lambda=513.0,
        #     description="Green channel of the microscope, 525/50 nm filter.",
        # )

        device_name = "BrukerFluorescenceMicroscope"
        description = f"Version {xml_metadata['version']}"
        metadata["Ophys"]["Device"][0].update(
            name=device_name,
            description=description,
        )

        imaging_plane_name = "GCaMP6f_functional"
        imaging_plane_metadata = metadata["Ophys"]["ImagingPlane"][
            0
        ]  # should it be photon_series_index pr imaging_plane_index
        imaging_plane_metadata.update(
            name=imaging_plane_name,
            # optical_channel=channel_name,
            device=device_name,
            excitation_lambda=920.0,
            indicator="GCaMP6f",
            imaging_rate=self.imaging_extractor.get_sampling_frequency(),
        )

        two_photon_series_metadata = metadata["Ophys"]["TwoPhotonSeries"][0]  # should it be photon_series_index
        two_photon_series_metadata.update(
            name="FunctionalGreenTwoPhotonSeries",
            imaging_plane=imaging_plane_name,
            format=".nii",
            scan_line_rate=1 / float(xml_metadata["scanLinePeriod"]),  # why I cannot see it in the NWBFile?
            rate=self.imaging_extractor.get_sampling_frequency(),
            description="Imaging data acquired (GCaMP6f) from the Bruker Two-Photon Microscope and transform to NIfTI. Used for functional imaging readout",
            unit="px",
            # device=device_name
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


class BrezovecFunctionalRedImagingInterface(BaseImagingExtractorInterface):
    """
    Data Interface for writing the functional imaging data (tdTomato) for Clandinin lab to NWB file using BrezovecMultiPlaneImagingExtractor.

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

        # channel_name = 'Red'
        # metadata["Ophys"]["OpticalChannel"][1].update(
        #     name=channel_name,
        #     emission_lambda=581.0,
        #     description="Red channel of the microscope, 550/50 nm filter.",
        # )

        device_name = "BrukerFluorescenceMicroscope"
        description = f"Version {xml_metadata['version']}"
        metadata["Ophys"]["Device"][0].update(
            name=device_name,
            description=description,
        )

        imaging_plane_name = "tdTomato_functional"
        imaging_plane_metadata = metadata["Ophys"]["ImagingPlane"][
            0
        ]  # should it be photon_series_index pr imaging_plane_index
        imaging_plane_metadata.update(
            name=imaging_plane_name,
            # optical_channel=channel_name,
            device=device_name,
            excitation_lambda=920.0,
            indicator="tdTomato",
            imaging_rate=self.imaging_extractor.get_sampling_frequency(),
        )

        two_photon_series_metadata = metadata["Ophys"]["TwoPhotonSeries"][0]
        two_photon_series_metadata.update(
            name="FunctionalRedTwoPhotonSeries",
            imaging_plane=imaging_plane_name,
            format=".nii",
            scan_line_rate=1 / float(xml_metadata["scanLinePeriod"]),  # why I cannot see it in the NWBFile?
            rate=self.imaging_extractor.get_sampling_frequency(),
            description="Imaging data acquired (tdTomato) from the Bruker Two-Photon Microscope and transform to NIfTI. Used for motion correction and registration.",  # TODO doucle check in the paper
            unit="px",
            # device=device_name
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


class BrezovecAnatomicalGreenImagingInterface(BaseImagingExtractorInterface):
    """
    Data Interface for writing the anatomical imaging data (GCaMP6f) for Clandinin lab to NWB file using BrezovecMultiPlaneImagingExtractor.
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

        # channel_name = 'Green'
        # metadata["Ophys"]["OpticalChannel"][0].update(
        #     name=channel_name,
        #     emission_lambda=513.0,
        #     description="Green channel of the microscope, 525/50 nm filter.",
        # )

        device_name = "BrukerFluorescenceMicroscope"
        description = f"Version {xml_metadata['version']}"
        metadata["Ophys"]["Device"][0].update(
            name=device_name,
            description=description,
        )

        imaging_plane_name = "GCaMP6f_anatomical"
        imaging_plane_metadata = metadata["Ophys"]["ImagingPlane"][
            0
        ]  # should it be photon_series_index pr imaging_plane_index
        imaging_plane_metadata.update(
            name=imaging_plane_name,
            # optical_channel=channel_name,
            device=device_name,
            excitation_lambda=920.0,
            indicator="GCaMP6f",
            imaging_rate=self.imaging_extractor.get_sampling_frequency(),
        )

        two_photon_series_metadata = metadata["Ophys"]["TwoPhotonSeries"][0]
        two_photon_series_metadata.update(
            name="AnatomicalGreenTwoPhotonSeries",
            imaging_plane=imaging_plane_name,
            format=".nii",
            scan_line_rate=1 / float(xml_metadata["scanLinePeriod"]),
            rate=self.imaging_extractor.get_sampling_frequency(),
            description="Imaging data acquired (GCaMP6f) from the Bruker Two-Photon Microscope and transform to NIfTI. Not used",  # TODO doucle check in the paper
            unit="px",
            # device=device_name
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


class BrezovecAnatomicalRedImagingInterface(BaseImagingExtractorInterface):
    """
    Data Interface for writing the anatomical imaging data (tdTomato) for Clandinin lab to NWB file using BrezovecMultiPlaneImagingExtractor.
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

        # channel_name = 'Red'
        # metadata["Ophys"]["OpticalChannel"][1].update(
        #     name=channel_name,
        #     emission_lambda=581.0,
        #     description="Red channel of the microscope, 550/50 nm filter.",
        # )

        device_name = "BrukerFluorescenceMicroscope"
        description = f"Version {xml_metadata['version']}"
        metadata["Ophys"]["Device"][0].update(
            name=device_name,
            description=description,
        )

        imaging_plane_name = "tdTomato_anatomical"
        imaging_plane_metadata = metadata["Ophys"]["ImagingPlane"][0]
        imaging_plane_metadata.update(
            name=imaging_plane_name,
            # optical_channel=channel_name,
            device=device_name,
            excitation_lambda=920.0,
            indicator="tdTomato",
            imaging_rate=self.imaging_extractor.get_sampling_frequency(),
        )

        two_photon_series_metadata = metadata["Ophys"]["TwoPhotonSeries"][0]
        two_photon_series_metadata.update(
            name="AnatomicalRedTwoPhotonSeries",
            imaging_plane=imaging_plane_name,
            format=".nii",
            scan_line_rate=1 / float(xml_metadata["scanLinePeriod"]),  # why I cannot see it in the NWBFile?
            rate=self.imaging_extractor.get_sampling_frequency(),
            description="Imaging data acquired (tdTomato) from the Bruker Two-Photon Microscope and transform to NIfTI. Used for primary anatomy",  # TODO doucle check in the paper
            unit="px"
            # device=device_name
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
