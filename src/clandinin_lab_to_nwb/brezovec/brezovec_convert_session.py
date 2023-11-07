"""Primary script to run to convert an entire session for of data using the NWBConverter."""
from pathlib import Path
from typing import Union
from datetime import datetime
from zoneinfo import ZoneInfo
import os
import itertools

from neuroconv.utils import load_dict_from_file, dict_deep_update
from dateutil import parser

from clandinin_lab_to_nwb.brezovec import BrezovecNWBConverter


def find_items_in_directory(directory: str, prefix: str, suffix: str):
    for item in os.listdir(directory):
        if item.startswith(prefix) and item.endswith(suffix):
            return os.path.join(directory, item)


def read_session_start_time_from_file(xml_file):
    from xml.etree import ElementTree

    date = None
    first_timestamp = None

    for event, elem in ElementTree.iterparse(xml_file, events=("start", "end")):
        # Extract the date from PVScan
        if date is None and elem.tag == "PVScan" and event == "end":
            date_string = elem.attrib.get("date")
            date = datetime.strptime(date_string, "%m/%d/%Y %H:%M:%S  %p")
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
        xml_file_path = Path(folder_path) / f"{Path(folder_path).name}.xml"

        imaging_purpose = "Functional" if "func" in imaging_type else "Anatomical"
        interface_name = f"Imaging{imaging_purpose}{channel}"
        source_data[interface_name] = {
            "folder_path": str(folder_path),
            "channel": channel,
            "imaging_purpose": imaging_purpose,
        }
        conversion_options[interface_name] = {"stub_test": stub_test, "photon_series_index": photon_series_index}
        photon_series_index += 1

    stub_frames = 5 if stub_test else None
    if stub_frames:
        interfaces_with_stub_frames = (
            "ImagingFunctionalGreen",
            "ImagingFunctionalRed",
            "ImagingAnatomicalGreen",
            "ImagingAnatomicalRed",
        )
        for interface in interfaces_with_stub_frames:
            conversion_options[interface]["stub_frames"] = stub_frames

    converter = BrezovecNWBConverter(source_data=source_data, verbose=verbose)

    metadata = converter.get_metadata()

    # Update default metadata with the editable in the corresponding yaml file
    editable_metadata_path = Path(__file__).parent / "brezovec_metadata.yaml"
    editable_metadata = load_dict_from_file(editable_metadata_path)
    metadata = dict_deep_update(metadata, editable_metadata)

    # Add datetime to conversion
    session_start_datetime = read_session_start_time_from_file(xml_file_path)
    timezone = ZoneInfo("America/Los_Angeles")  # Time zone for Stanford, California
    localized_date = session_start_datetime.replace(tzinfo=timezone)
    metadata = dict_deep_update(
        metadata, {"NWBFile": {"session_start_time": localized_date}, "Subject": {"subject_id": subject_id}}
    )

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
