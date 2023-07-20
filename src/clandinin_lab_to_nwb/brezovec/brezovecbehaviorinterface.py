"""Primary class for converting experiment-specific behavior."""
from pathlib import Path
from pynwb.file import NWBFile
from hdmf.backends.hdf5.h5_utils import H5DataIO
from neuroconv.utils.json_schema import FolderPathType, FilePathType
from neuroconv.tools.nwb_helpers import get_module
from pynwb.behavior import SpatialSeries
import polars as pl


from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.utils import DeepDict


class FicTracInterface(BaseDataInterface):
    """Behavior interface for Fictrack data as described in https://github.com/rjdmoore/fictrac"""

    keywords = [
        "fictrack",
        "visual tracking",
        "fictive path",
        "spherical treadmill",
        "visual fixation",
    ]

    # Taken from https://github.com/rjdmoore/fictrac/blob/master/doc/data_header.txt
    column_to_description = {
        "frame_counter": "Corresponding video frame (starts at #1).",
        "cam_delta_rotation_vector_x_right": "Change in orientation since last frame, represented as rotation angle/axis (radians) in camera coordinates (x right).",
        "cam_delta_rotation_vector_y_down": "Change in orientation since last frame, represented as rotation angle/axis (radians) in camera coordinates (y down).",
        "cam_delta_rotation_vector_z_forward": "Change in orientation since last frame, represented as rotation angle/axis (radians) in camera coordinates (z forward).",
        "delta_rotation_error_score": "Error score associated with rotation estimate.",
        "lab_delta_rotation_vector_x_right": "Change in orientation since last frame, represented as rotation angle/axis (radians) in laboratory coordinates (x right).",
        "lab_delta_rotation_vector_y_down": "Change in orientation since last frame, represented as rotation angle/axis (radians) in laboratory coordinates (y down).",
        "lab_delta_rotation_vector_z_forward": "Change in orientation since last frame, represented as rotation angle/axis (radians) in laboratory coordinates (z forward).",
        "cam_absolute_rotation_vector_x": "Absolute orientation of the sphere represented as rotation angle/axis (radians) in camera coordinates (x).",
        "cam_absolute_rotation_vector_y": "Absolute orientation of the sphere represented as rotation angle/axis (radians) in camera coordinates (y).",
        "cam_absolute_rotation_vector_z": "Absolute orientation of the sphere represented as rotation angle/axis (radians) in camera coordinates (z).",
        "lab_absolute_rotation_vector_x": "Absolute orientation of the sphere represented as rotation angle/axis (radians) in laboratory coordinates (x).",
        "lab_absolute_rotation_vector_y": "Absolute orientation of the sphere represented as rotation angle/axis (radians) in laboratory coordinates (y).",
        "lab_absolute_rotation_vector_z": "Absolute orientation of the sphere represented as rotation angle/axis (radians) in laboratory coordinates (z).",
        "lab_integrated_x_y_position_x": "Integrated x position (radians) in laboratory coordinates. Scale by sphere radius for true position.",
        "lab_integrated_x_y_position_y": "Integrated y position (radians) in laboratory coordinates. Scale by sphere radius for true position.",
        "lab_integrated_animal_heading": "Integrated heading orientation (radians) of the animal in laboratory coordinates. This is the direction the animal is facing.",
        "lab_animal_movement_direction": "Instantaneous running direction (radians) of the animal in laboratory coordinates. This is the direction the animal is moving in the lab frame (add to animal heading to get direction in the world).",
        "animal_movement_speed": "Instantaneous running speed (radians/frame) of the animal. Scale by sphere radius for true speed.",
        "integrated_forward_side_motion_x": "Integrated x position (radians) of the sphere in laboratory coordinates neglecting heading. Equivalent to the output from two optic mice.",
        "integrated_forward_side_motion_y": "Integrated y position (radians) of the sphere in laboratory coordinates neglecting heading. Equivalent to the output from two optic mice.",
        "timestamp": "Either position in video file (ms) or frame capture time (ms since epoch).",
        "sequence_counter": "Position in the current frame sequence. Usually corresponds directly to the frame counter, but can reset to 1 if tracking is reset.",
        "delta_timestamps": "Time (ms) since the last frame.",
        "alt_timestamp": "Frame capture time (ms since midnight).",
    }

    int_type_columns = ["sequence_counter", "frame_counter"]

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        assert self.file_path.is_file(), f"File path does not exist: {self.file_path}"

        # This should load the data lazily and prepare variables you need
        pass

    def get_metadata(self) -> DeepDict:
        # Automatically retrieve as much metadata as possible
        metadata = super().get_metadata()

        return metadata

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict):
        # All the custom code to write to PyNWB

        descriptions = FicTracInterface.column_to_description
        columns = list(descriptions)[:23]

        int_type_columns = FicTracInterface.int_type_columns
        column_to_type = lambda x: pl.Int64 if x in int_type_columns else pl.Float64

        polars_schema = {column: column_to_type(column) for column in columns}
        df_fitrac = pl.scan_csv(
            self.file_path,
            has_header=False,
            new_columns=columns,
            dtypes=polars_schema,
            separator=",",
            encoding="utf8",
        )

        # This is the difference between each timestamp in average
        time_delta = df_fitrac.select(pl.col("timestamp").diff().mean()).collect().item()
        sampling_rate = 1000.0 / time_delta

        description = "Fictrac data"
        processing_module = get_module(nwbfile=nwbfile, name="Behavior", description=description)

        # Select the columns in cam_delta_rotation_columns
        cam_delta_rotation_columns = [
            "cam_delta_rotation_vector_x_right",
            "cam_delta_rotation_vector_y_down",
            "cam_delta_rotation_vector_z_forward",
        ]
        df_cam_delta_rotation = df_fitrac.select(cam_delta_rotation_columns).collect()

        reference_frame = "camera"
        data = df_cam_delta_rotation.to_numpy()
        spatial_series = SpatialSeries(
            name="cam_delta_rotation", data=data, reference_frame=reference_frame, rate=sampling_rate
        )
        processing_module.add_data_interface(spatial_series)

        # Select the columns in lab_delta_rotation_columns
        lab_delta_rotation = [
            "lab_delta_rotation_vector_x_right",
            "lab_delta_rotation_vector_y_down",
            "lab_delta_rotation_vector_z_forward",
        ]
        df_lab_delta_rotation = df_fitrac.select(lab_delta_rotation).collect()

        reference_frame = "laboratory"
        data = df_lab_delta_rotation.to_numpy()
        spatial_series = SpatialSeries(
            name="lab_delta_rotation", data=data, reference_frame=reference_frame, rate=sampling_rate
        )

        processing_module.add_data_interface(spatial_series)

        # Select the columns in cam_absolute_rotation_columns
        cam_absolute_rotation = [
            "cam_absolute_rotation_vector_x",
            "cam_absolute_rotation_vector_y",
            "cam_absolute_rotation_vector_z",
        ]
        df_cam_absolute_rotation = df_fitrac.select(cam_absolute_rotation).collect()

        reference_frame = "camera"
        data = df_cam_absolute_rotation.to_numpy()
        spatial_series = SpatialSeries(
            name="cam_absolute_rotation", data=data, reference_frame=reference_frame, rate=sampling_rate
        )

        processing_module.add_data_interface(spatial_series)

        # Select the columns in lab_absolute_rotation_columns
        lab_absolute_rotation = [
            "lab_absolute_rotation_vector_x",
            "lab_absolute_rotation_vector_y",
            "lab_absolute_rotation_vector_z",
        ]
        df_lab_absolute_rotation = df_fitrac.select(lab_absolute_rotation).collect()

        reference_frame = "laboratory"
        data = df_lab_absolute_rotation.to_numpy()
        spatial_series = SpatialSeries(
            name="lab_absolute_rotation", data=data, reference_frame=reference_frame, rate=sampling_rate
        )

        processing_module.add_data_interface(spatial_series)

        # Select the columns in lab_integrated_x_y_position
        lab_integrated_x_y_position = ["lab_integrated_x_y_position_x", "lab_integrated_x_y_position_y"]
        df_lab_integrated_x_y_position = df_fitrac.select(lab_integrated_x_y_position).collect()

        reference_frame = "laboratory"
        data = df_lab_integrated_x_y_position.to_numpy()
        spatial_series = SpatialSeries(
            name="lab_integrated_x_y_position", data=data, reference_frame=reference_frame, rate=sampling_rate
        )

        processing_module.add_data_interface(spatial_series)

        # Lab integrated animal heading
        lab_integrated_animal_heading = ["lab_integrated_animal_heading"]
        df_lab_integrated_animal_heading = df_fitrac.select(lab_integrated_animal_heading).collect()

        reference_frame = "laboratory"
        data = df_lab_integrated_animal_heading.to_numpy()
        spatial_series = SpatialSeries(
            name="lab_integrated_animal_heading", data=data, reference_frame=reference_frame, rate=sampling_rate
        )

        processing_module.add_data_interface(spatial_series)

        # lab_animal_movement_direction
        lab_animal_movement_direction = ["lab_animal_movement_direction"]
        df_lab_animal_movement_direction = df_fitrac.select(lab_animal_movement_direction).collect()

        reference_frame = "laboratory"
        data = df_lab_animal_movement_direction.to_numpy()
        spatial_series = SpatialSeries(
            name="lab_animal_movement_direction", data=data, reference_frame=reference_frame, rate=sampling_rate
        )

        processing_module.add_data_interface(spatial_series)

        # animal_movement_speed
        animal_movement_speed = ["animal_movement_speed"]
        df_animal_movement_speed = df_fitrac.select(animal_movement_speed).collect()

        reference_frame = "laboratory"
        data = df_animal_movement_speed.to_numpy()
        spatial_series = SpatialSeries(
            name="animal_movement_speed", data=data, reference_frame=reference_frame, rate=sampling_rate
        )

        processing_module.add_data_interface(spatial_series)

        # integrated_forward_side_motion
        integrated_forward_side_motion = ["integrated_forward_side_motion_x", "integrated_forward_side_motion_y"]
        df_integrated_forward_side_motion = df_fitrac.select(integrated_forward_side_motion).collect()

        reference_frame = "laboratory"
        data = df_integrated_forward_side_motion.to_numpy()
        spatial_series = SpatialSeries(
            name="integrated_forward_side_motion", data=data, reference_frame=reference_frame, rate=sampling_rate
        )

        processing_module.add_data_interface(spatial_series)

        behavior_description = "Behavior data from Fictrack"
        processing_module = get_module(nwbfile=nwbfile, name="behavior", description=behavior_description)

        return nwbfile

    @staticmethod
    def fictrac_data_generator(file_path: str):
        file_path = Path(file_path)

        int_type_columns = ["sequence_counter", "frame_counter"]
        columns_name_in_order = list(FicTracInterface.column_to_description.keys())
        with file_path.open("r", encoding="UTF-8") as file:
            for line in file:
                line = line.strip()
                row_values = line.split(",")
                row_data_dict = {}
                for index, value in enumerate(row_values):
                    column = columns_name_in_order[index]

                    # The values are string so we need to cast them to the correct type
                    if column in int_type_columns:
                        value = int(value) if value is not None else None
                    else:
                        value = float(value) if value is not None else None

                    row_data_dict[column] = value

                yield row_data_dict
