"""Primary script to run to convert an entire session for of data using the NWBConverter."""
from pathlib import Path
from typing import Union
import datetime
from zoneinfo import ZoneInfo

from neuroconv.utils import load_dict_from_file, dict_deep_update

from clandinin_lab_to_nwb.brezovec import BrezovecNWBConverter


def session_to_nwb(data_dir_path: Union[str, Path], output_dir_path: Union[str, Path], stub_test: bool = False):
    data_dir_path = Path(data_dir_path)
    output_dir_path = Path(output_dir_path)
    if stub_test:
        output_dir_path = output_dir_path / "nwb_stub"
    output_dir_path.mkdir(parents=True, exist_ok=True)

    session_id = "subject_identifier_usually"
    nwbfile_path = output_dir_path / f"{session_id}.nwb"

    source_data = dict()
    conversion_options = dict()

    # Add Fictrac
    file_path = data_dir_path / "fictrac" / "fictrac-20200228_161226.dat"
    source_data.update(dict(FicTrac=dict(file_path=str(file_path))))

    converter = BrezovecNWBConverter(source_data=source_data)

    # Add datetime to conversion
    metadata = converter.get_metadata()
    datetime.datetime(year=2020, month=1, day=1, tzinfo=ZoneInfo("US/Eastern"))
    date = datetime.datetime.today()  # TO-DO: Get this from author
    metadata["NWBFile"]["session_start_time"] = date

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
    root_path = Path("/home/heberto/Clandinin-CN-data-share/")
    data_dir_path = root_path / "brezovec_example_data"
    output_dir_path = Path("/home/heberto/conversion_nwb/")
    stub_test = False

    session_to_nwb(
        data_dir_path=data_dir_path,
        output_dir_path=output_dir_path,
        stub_test=stub_test,
    )
