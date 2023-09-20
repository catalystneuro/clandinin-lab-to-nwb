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

    # # Add Fictrac
    # file_path = data_dir_path / "fictrac" / "fictrac-20200228_161226.dat"
    # source_data.update(dict(FicTrac=dict(file_path=str(file_path))))

    # Add Green Channel Functional Imaging
    folder_path = data_dir_path / "func_0" / "TSeries-06202020-0931-003"
    source_data.update(dict(OphysGreenFun=dict(folder_path=str(folder_path), stream_name="Green")))
    conversion_options.update(dict(OphysGreenFun=dict(stub_test=True, stub_frames=10, photon_series_index=0)))

    # Add Red Channel Functional Imaging
    source_data.update(dict(OphysRedFun=dict(folder_path=str(folder_path), stream_name="Red")))
    conversion_options.update(dict(OphysRedFun=dict(stub_test=True, stub_frames=10, photon_series_index=1)))

    # Add Green Channel Anatomical Imaging
    folder_path = data_dir_path / "anat_0" / "TSeries-06202020-0931-004"
    source_data.update(dict(OphysGreenAna=dict(folder_path=str(folder_path), stream_name="Green")))
    conversion_options.update(dict(OphysGreenAna=dict(stub_test=True, stub_frames=10, photon_series_index=2)))

    # Add Red Channel Anatomical Imaging
    source_data.update(dict(OphysRedAna=dict(folder_path=str(folder_path), stream_name="Red")))
    conversion_options.update(dict(OphysRedAna=dict(stub_test=True, stub_frames=10, photon_series_index=3)))

    converter = BrezovecNWBConverter(source_data=source_data)

    # Add datetime to conversion
    metadata = converter.get_metadata()
    date = datetime.datetime(year=2020, month=1, day=1, tzinfo=ZoneInfo("US/Eastern"))
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
    root_path = Path("/media/amtra/Samsung_T5/CN_data/")
    # root_path = Path("/home/heberto/Clandinin-CN-data-share/")
    data_dir_path = root_path / "brezovec_example_data/imports/20200620/fly2"
    output_dir_path = root_path / "conversion_nwb"
    stub_test = True

    session_to_nwb(
        data_dir_path=data_dir_path,
        output_dir_path=output_dir_path,
        stub_test=stub_test,
    )
