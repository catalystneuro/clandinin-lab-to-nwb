"""Primary script to run to convert an entire session for of data using the NWBConverter."""
from pathlib import Path
from typing import Union
import os
import itertools

from neuroconv.utils import load_dict_from_file, dict_deep_update

from clandinin_lab_to_nwb.brezovec import BrezovecNWBConverter


def find_items_in_directory(directory: str, prefix: str, suffix: str):
    for item in os.listdir(directory):
        if item.startswith(prefix) and item.endswith(suffix):
            return os.path.join(directory, item)


def session_to_nwb(
    data_dir_path: Union[str, Path],
    output_dir_path: Union[str, Path],
    subject_id: str,
    session_id: str,
    stub_test: bool = False,
    verbose: bool = False,
):
    if verbose:
        print(f"Converting session {session_id} for subject {subject_id}")

    data_dir_path = Path(data_dir_path)
    output_dir_path = Path(output_dir_path)
    if stub_test:
        output_dir_path = output_dir_path / "nwb_stub"
    output_dir_path.mkdir(parents=True, exist_ok=True)

    nwbfile_path = output_dir_path / f"{session_id}.nwb"

    source_data = dict()
    conversion_options = dict()

    # Add Fictrac
    directory = data_dir_path / "fictrac"
    prefix = f"fictrac-{session_id}"
    suffix = ".dat"
    file_path = find_items_in_directory(directory=directory, prefix=prefix, suffix=suffix)
    diameter_mm = 9.0  # From the Brezovec paper
    diameter_meters = diameter_mm / 1000.0
    source_data.update(dict(FicTrac=dict(file_path=str(file_path), radius=diameter_meters / 2)))

    # Video
    suffix = "-raw.avi"
    file_path = find_items_in_directory(directory=directory, prefix=prefix, suffix=suffix)
    file_paths = [file_path]
    source_data.update(dict(Video=dict(file_paths=file_paths)))
    conversion_options.update(dict(Video=dict(stub_test=stub_test)))

    # Determine the correct directories and add Functional and Anatomical Imaging data
    photon_series_index = 0
    for imaging_type, channel in itertools.product(["func_0", "anat_0"], ["Green", "Red"]):
        directory = data_dir_path / "imports" / session_id / subject_id / imaging_type
        folder_path = find_items_in_directory(directory=directory, prefix="TSeries-", suffix="")

        imaging_purpose = "Functional" if "func" in imaging_type else "Anatomical"
        interface_name = f"Imaging{imaging_purpose}{channel}"
        source_data[interface_name] = {
            "folder_path": str(folder_path),
            "channel": channel,
            "imaging_purpose": imaging_purpose,
        }
        conversion_options[interface_name] = {"stub_test": stub_test, "photon_series_index": photon_series_index}
        if stub_test:
            stub_frames = 5
            conversion_options[interface_name]["stub_frames"] = stub_frames
        photon_series_index += 1

    converter = BrezovecNWBConverter(source_data=source_data, verbose=verbose)

    metadata = converter.get_metadata()

    # Update default metadata with the editable in the corresponding yaml file
    editable_metadata_path = Path(__file__).parent / "brezovec_metadata.yaml"
    editable_metadata = load_dict_from_file(editable_metadata_path)
    metadata = dict_deep_update(metadata, editable_metadata)

    # Add the correct subject ID
    metadata = dict_deep_update(metadata, {"Subject": {"subject_id": subject_id}})

    # Run conversion
    converter.run_conversion(
        metadata=metadata,
        nwbfile_path=nwbfile_path,
        conversion_options=conversion_options,
        overwrite=True,
    )


if __name__ == "__main__":
    from pathlib import Path
    from clandinin_lab_to_nwb.brezovec.brezovec_convert_session import session_to_nwb

    root_path = Path.home() / "Clandinin-CN-data-share"  # Change this to the directory where the data is stored
    data_dir_path = root_path / "brezovec_example_data"
    output_dir_path = Path.home() / "conversion_nwb"
    stub_test = True  # Set to False to convert the full session
    verbose = True
    session_id = "20200620"
    subject_id = "fly2"

    # Note this assumes that the files are arranged in the same way as in the example data
    session_to_nwb(
        data_dir_path=data_dir_path,
        output_dir_path=output_dir_path,
        stub_test=stub_test,
        session_id=session_id,
        subject_id=subject_id,
        verbose=verbose,
    )
