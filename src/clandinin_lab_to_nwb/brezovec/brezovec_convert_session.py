"""Primary script to run to convert an entire session for of data using the NWBConverter."""
from pathlib import Path
from typing import Union
from datetime import datetime
from zoneinfo import ZoneInfo
import os
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
):
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
    source_data.update(dict(FicTrac=dict(file_path=str(file_path))))

    # Video
    suffix = "-raw.avi"
    file_path = find_items_in_directory(directory=directory, prefix=prefix, suffix=suffix)
    file_paths = [file_path]
    source_data.update(dict(Video=dict(file_paths=file_paths)))
    conversion_options.update(dict(Video=dict(stub_test=stub_test)))

    stub_frames = 10 if stub_test else None

    # Select correct folder for Functional Imaging
    directory = data_dir_path / "imports" / session_id / subject_id / "func_0"
    prefix = f"TSeries-"
    suffix = ""
    folder_path = find_items_in_directory(directory=directory, prefix=prefix, suffix=suffix)

    xml_file_path = Path(folder_path) / f"{Path(folder_path).name}.xml"

    # Add Green Channel Functional Imaging
    source_data.update(dict(ImagingFunctionalGreen=dict(folder_path=str(folder_path), stream_name="Green")))
    conversion_options.update(
        dict(ImagingFunctionalGreen=dict(stub_test=stub_test, stub_frames=stub_frames, photon_series_index=0))
    )

    # Add Red Channel Functional Imaging
    source_data.update(dict(ImagingFunctionalRed=dict(folder_path=str(folder_path), stream_name="Red")))
    conversion_options.update(
        dict(ImagingFunctionalRed=dict(stub_test=stub_test, stub_frames=stub_frames, photon_series_index=1))
    )

    # Select correct folder for Anatomical Imaging
    directory = data_dir_path / "imports" / session_id / subject_id / "anat_0"
    folder_path = find_items_in_directory(directory=directory, prefix=prefix, suffix=suffix)

    # Add Green Channel Anatomical Imaging
    source_data.update(dict(ImagingAnatomicalGreen=dict(folder_path=str(folder_path), stream_name="Green")))
    conversion_options.update(
        dict(ImagingAnatomicalGreen=dict(stub_test=stub_test, stub_frames=stub_frames, photon_series_index=2))
    )

    # Add Red Channel Anatomical Imaging
    source_data.update(dict(ImagingAnatomicalRed=dict(folder_path=str(folder_path), stream_name="Red")))
    conversion_options.update(
        dict(ImagingAnatomicalRed=dict(stub_test=stub_test, stub_frames=stub_frames, photon_series_index=3))
    )

    converter = BrezovecNWBConverter(source_data=source_data)

    metadata = converter.get_metadata()

    # Update default metadata with the editable in the corresponding yaml file
    editable_metadata_path = Path(__file__).parent / "brezovec_metadata.yaml"
    editable_metadata = load_dict_from_file(editable_metadata_path)
    metadata = dict_deep_update(metadata, editable_metadata)

    # Add datetime to conversion
    session_start_datetime = read_session_start_time_from_file(xml_file_path)
    timezone = ZoneInfo("America/Los_Angeles")  # Time zone for Stanford, California
    localized_date = session_start_datetime.replace(tzinfo=timezone)
    metadata["NWBFile"]["session_start_time"] = localized_date
    metadata["Subject"]["subject_id"] = subject_id

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
    output_dir_path = Path.home() / "conversion_nwb"
    stub_test = True
    session_id = "20200620"
    subject_id = "fly2"

    session_to_nwb(
        data_dir_path=data_dir_path,
        output_dir_path=output_dir_path,
        stub_test=stub_test,
        session_id=session_id,
        subject_id=subject_id,
    )
