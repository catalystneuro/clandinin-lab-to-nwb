"""Primary script to run to convert an entire session for of data using the NWBConverter."""
from pathlib import Path
from typing import Union
import datetime
from zoneinfo import ZoneInfo
import os
from neuroconv.utils import load_dict_from_file, dict_deep_update

from clandinin_lab_to_nwb.brezovec import BrezovecNWBConverter


def find_items_in_directory(directory: str, prefix: str, suffix: str):
    for item in os.listdir(directory):
        if item.startswith(prefix) and item.endswith(suffix):
            return os.path.join(directory, item)


def session_to_nwb(data_dir_path: Union[str, Path], output_dir_path: Union[str, Path], subject_id: str, session_id: str, stub_test: bool = False):
    data_dir_path = Path(data_dir_path)
    output_dir_path = Path(output_dir_path)
    if stub_test:
        output_dir_path = output_dir_path / "nwb_stub"
    output_dir_path.mkdir(parents=True, exist_ok=True)

    # Parse date from session_id
    parsed_date = datetime.datetime.strptime(session_id, "%Y%m%d")
    nwbfile_path = output_dir_path / f"{session_id}.nwb"

    source_data = dict()
    conversion_options = dict()

    # Add Fictrac
    directory = data_dir_path / "fictrac"
    prefix = f"fictrac-{session_id}"
    suffix = ".dat"
    file_path = find_items_in_directory(directory=directory, prefix=prefix, suffix=suffix)
    source_data.update(dict(FicTrac=dict(file_path=str(file_path))))

    # Video
    suffix = "-raw.avi"
    file_path = find_items_in_directory(directory=directory, prefix=prefix, suffix=suffix)
    file_paths = [file_path]
    source_data.update(dict(Video=dict(file_paths=file_paths)))
    conversion_options.update(dict(Video=dict(stub_test=stub_test)))

    # Select correct folder for Functional Imaging
    directory = data_dir_path / "imports" / session_id / subject_id / "func_0"
    prefix = f"TSeries-"
    suffix = ""
    folder_path = find_items_in_directory(directory=directory, prefix=prefix, suffix=suffix)

    # Add Green Channel Functional Imaging
    source_data.update(dict(ImagingFunctionalGreen=dict(folder_path=str(folder_path), stream_name="Green")))
    conversion_options.update(
        dict(ImagingFunctionalGreen=dict(stub_test=stub_test, stub_frames=10, photon_series_index=0)) #TODO: remove stub_frames
    )

    # Add Red Channel Functional Imaging
    source_data.update(dict(ImagingFunctionalRed=dict(folder_path=str(folder_path), stream_name="Red")))
    conversion_options.update(
        dict(ImagingFunctionalRed=dict(stub_test=stub_test, stub_frames=10, photon_series_index=1))
    )

    # Select correct folder for Anatomical Imaging
    directory = data_dir_path / "imports" / session_id / subject_id / "anat_0"
    folder_path = find_items_in_directory(directory=directory, prefix=prefix, suffix=suffix)

    # Add Green Channel Anatomical Imaging
    source_data.update(dict(ImagingAnatomicalGreen=dict(folder_path=str(folder_path), stream_name="Green")))
    conversion_options.update(
        dict(ImagingAnatomicalGreen=dict(stub_test=stub_test, stub_frames=10, photon_series_index=2))
    )

    # Add Red Channel Anatomical Imaging
    source_data.update(dict(ImagingAnatomicalRed=dict(folder_path=str(folder_path), stream_name="Red")))
    conversion_options.update(
        dict(ImagingAnatomicalRed=dict(stub_test=stub_test, stub_frames=10, photon_series_index=3))
    )

    converter = BrezovecNWBConverter(source_data=source_data)

    # Add datetime to conversion
    metadata = converter.get_metadata()
    tzinfo = ZoneInfo("America/Los_Angeles")  # Time zone for Stanford, California
    date = parsed_date.replace(tzinfo=tzinfo)
    metadata["NWBFile"]["session_start_time"] = date
    metadata["Subject"]["subject_id"] = subject_id

    # Update default metadata with the editable in the corresponding yaml file
    editable_metadata_path = Path(__file__).parent / "brezovec_metadata.yaml"
    editable_metadata = load_dict_from_file(editable_metadata_path)
    metadata = dict_deep_update(metadata, editable_metadata)

    # Run conversion
    converter.run_conversion(
        metadata=metadata,
        nwbfile_path=nwbfile_path,
        conversion_options=conversion_options,
        overwrite=True,
    )


if __name__ == "__main__":
    # Parameters for conversion
    root_path = Path("/media/amtra/Samsung_T5/CN_data/")
    # root_path = Path("/home/heberto/Clandinin-CN-data-share/")
    data_dir_path = root_path / "brezovec_example_data"
    output_dir_path = root_path / "conversion_nwb"
    stub_test = True

    session_to_nwb(
        data_dir_path=data_dir_path,
        output_dir_path=output_dir_path,
        stub_test=stub_test,
    )
