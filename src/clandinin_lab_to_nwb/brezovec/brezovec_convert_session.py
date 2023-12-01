"""Primary script to run to convert an entire session for of data using the NWBConverter."""
from pathlib import Path
from typing import Union
import itertools
from zoneinfo import ZoneInfo

from neuroconv.utils import load_dict_from_file, dict_deep_update

from clandinin_lab_to_nwb.brezovec import BrezovecNWBConverter
from clandinin_lab_to_nwb.brezovec.brezovecimaginginterface import BrezovecImagingInterface


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

    # Determine the correct directories and add Functional and Anatomical Imaging data
    photon_series_index = 0
    imaging_purpose_mapping = dict(func_0="Functional", anat_0="Anatomical")
    for imaging_type, channel in itertools.product(["func_0", "anat_0"], ["Green", "Red"]):
        directory = data_dir_path / "imports" / session_id / subject_id / imaging_type
        imaging_folders_in_directory = (path for path in directory.iterdir() if path.is_dir())
        folder_path = next(path for path in imaging_folders_in_directory if "TSeries" in path.name)

        imaging_purpose = imaging_purpose_mapping[imaging_type]
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

    # Get the session start time from the Functional Green imaging data
    folder_path = source_data["ImagingFunctionalGreen"]["folder_path"]
    xml_file_path = Path(folder_path) / f"{Path(folder_path).name}.xml"
    functional_imaging_datetime = BrezovecImagingInterface.read_session_start_time_from_file(xml_file_path)
    hours_minutes_string = functional_imaging_datetime.strftime("%H%M")

    # Add Fictrac
    fictrac_directory = data_dir_path / "fictrac"
    fictrac_files = (path for path in fictrac_directory.iterdir() if path.suffix == ".dat")
    pattern = f"fictrac-{session_id}_{hours_minutes_string}"
    fictrac_file_path = [path for path in fictrac_files if pattern in path.name]
    assert len(fictrac_file_path) == 1, f"Expected to find a single FicTrac file with pattern {pattern}"
    fictrac_file_path = fictrac_file_path[0]
    diameter_mm = 9.0  # From the Brezovec paper
    diameter_meters = diameter_mm / 1000.0
    source_data.update(dict(FicTrac=dict(file_path=str(fictrac_file_path), radius=diameter_meters / 2)))

    # Video
    video_file_path = fictrac_file_path.with_name(fictrac_file_path.stem + "-raw.avi")
    file_paths = [video_file_path]
    source_data.update(dict(Video=dict(file_paths=file_paths)))
    conversion_options.update(dict(Video=dict(stub_test=stub_test)))

    converter = BrezovecNWBConverter(source_data=source_data, verbose=verbose)

    metadata = converter.get_metadata()

    # Update default metadata with the editable in the corresponding yaml file
    editable_metadata_path = Path(__file__).parent / "brezovec_metadata.yaml"
    editable_metadata = load_dict_from_file(editable_metadata_path)
    metadata = dict_deep_update(metadata, editable_metadata)

    # Add the correct metadata for the session
    timezone = ZoneInfo("America/Los_Angeles")  # Time zone for Stanford, California
    session_start_time = functional_imaging_datetime.replace(tzinfo=timezone)
    metadata["NWBFile"]["session_start_time"] = session_start_time
    metadata["Subject"]["subject_id"] = subject_id

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
    root_path = Path("/media/heberto/One Touch/Clandinin-CN-data-share")
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
