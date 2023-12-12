"""Primary script to run to convert an entire session for of data using the NWBConverter."""
from pathlib import Path
from typing import Union
import itertools
from zoneinfo import ZoneInfo
from datetime import datetime
import time

from neuroconv.utils import load_dict_from_file, dict_deep_update

from clandinin_lab_to_nwb.brezovec import BrezovecNWBConverter
from clandinin_lab_to_nwb.brezovec.brezovecimaginginterface import BrezovecImagingInterface


def session_to_nwb(
    data_dir_path: Union[str, Path],
    output_dir_path: Union[str, Path],
    subject_id: str,
    date_string: str,
    stub_test: bool = False,
    verbose: bool = False,
):
    start_time = time.time()
    data_dir_path = Path(data_dir_path)
    output_dir_path = Path(output_dir_path)
    if stub_test:
        output_dir_path = output_dir_path / "nwb_stub"
    output_dir_path.mkdir(parents=True, exist_ok=True)

    source_data = dict()
    conversion_options = dict()
    # Determine the correct directories and add Functional and Anatomical Imaging data
    photon_series_index = 0
    imaging_purpose_mapping = dict(func_0="Functional", anat_0="Anatomical")
    for imaging_type, channel in itertools.product(["func_0", "anat_0"], ["Green", "Red"]):
        directory = data_dir_path / "imports" / date_string / subject_id / imaging_type
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

    # Add Fictrac
    fictrac_directory = data_dir_path / "fictrac"
    fictrac_files = (path for path in fictrac_directory.iterdir() if path.suffix == ".dat")
    pattern = f"fictrac-{date_string}"
    # All of these files share the date_string
    fictrac_file_path_list = [path for path in fictrac_files if pattern in path.name]
    # The file names have a structure that is fictract-YYYYMMDDHHMMSS.dat
    # So to get the closest file to the functional imaging we need to convert the datetime strings to datetime objects
    # and then find the closest one
    datetime_strings = [p.stem.replace("fictrac-", "").replace("_", "") for p in fictrac_file_path_list]
    datetimes = [datetime.strptime(string, "%Y%m%d%H%M%S") for string in datetime_strings]
    time_differences = [abs((x - functional_imaging_datetime).total_seconds()) for x in datetimes]
    closest_index = time_differences.index(min(time_differences))
    fictrac_file_path = fictrac_file_path_list[closest_index]
    diameter_mm = 9.0  # From the Brezovec paper
    diameter_meters = diameter_mm / 1000.0
    source_data.update(dict(FicTrac=dict(file_path=str(fictrac_file_path), radius=diameter_meters / 2)))

    # Video
    video_file_path = fictrac_file_path.with_name(fictrac_file_path.stem + "-raw.avi")
    file_paths = [video_file_path]
    source_data.update(dict(Video=dict(file_paths=file_paths)))
    conversion_options.update(dict(Video=dict(stub_test=stub_test)))

    # Use the datestring as a session id
    session_id = datetime_strings[closest_index]
    # Get the subject id from the json mapping provided by the authors
    json_file_path = Path(__file__).parent / "subject_mapping.json"
    subject_mapping = load_dict_from_file(json_file_path)
    subject_id_without_underscores = subject_id.replace("_", "")
    fly = subject_mapping[date_string][subject_id_without_underscores]
    subject_id = fly

    if verbose:
        print("-" * 80)
        print(f"Converting session {session_id} for subject {subject_id}")

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
    metadata["NWBFile"]["session_id"] = session_id

    if verbose:
        print("The session start time from the functional imaging data is:")
        print(session_start_time)
        print("Transforming the following file_path of fictrac data:")
        print(fictrac_file_path.name)
        print("And the following file_paths of video data:")
        print(video_file_path.name)
        print("And the following folder_paths of imaging data:")
        for interface_name, interface_metadata in source_data.items():
            if "Imaging" in interface_name:
                print(f"{interface_name}: {Path(interface_metadata['folder_path']).name}")

    # Run conversion
    nwbfile_path = output_dir_path / f"{subject_id}.nwb"
    converter.run_conversion(
        metadata=metadata,
        nwbfile_path=nwbfile_path,
        conversion_options=conversion_options,
        overwrite=True,
    )

    end_time = time.time()
    if verbose:
        conversion_time = end_time - start_time
        conversion_time_minutes = conversion_time / 60.0
        print(f"Conversion took {conversion_time_minutes:.2f} minutes or {conversion_time:.2f} seconds")


if __name__ == "__main__":
    from pathlib import Path
    from clandinin_lab_to_nwb.brezovec.brezovec_convert_session import session_to_nwb

    root_path = Path.home() / "Clandinin-CN-data-share"  # Change this to the directory where the data is stored
    root_path = Path("/media/heberto/One Touch/Clandinin-CN-data-share")
    data_dir_path = root_path / "brezovec_example_data"
    output_dir_path = root_path / "conversion_nwb"
    stub_test = True  # Set to False to convert the full session
    verbose = True
    date_string = "20200627"
    subject_id = "fly_4"

    # Note this assumes that the files are arranged in the same way as in the example data
    session_to_nwb(
        data_dir_path=data_dir_path,
        output_dir_path=output_dir_path,
        stub_test=stub_test,
        date_string=date_string,
        subject_id=subject_id,
        verbose=verbose,
    )
