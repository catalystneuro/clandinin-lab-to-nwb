from pathlib import Path
from clandinin_lab_to_nwb.brezovec.brezovec_convert_session import session_to_nwb

from neuroconv.tools.path_expansion import LocalPathExpander

# Define rooth path and data directory
root_path = Path.home() / "Clandinin-CN-data-share"  # Change this to the directory where the data is stored
data_dir_path = root_path / "brezovec_example_data"
output_dir_path = root_path / "conversion_nwb"
stub_test = False  # Set to False to convert the full session, otherwise only a stub will be converted for testing
verbose = True

# Specify source data (note this assumes the files are arranged in the same way as in the example data)
base_directory = data_dir_path
source_data_spec = {
    "imaging": {
        "base_directory": base_directory,
        "folder_path": "imports/{date_string}/{subject_id}",
    }
}

# Instantiate LocalPathExpander
path_expander = LocalPathExpander()

# Expand paths and extract metadata
metadata_list = path_expander.expand_paths(source_data_spec)
# Filter over directories
metadata_list = [m for m in metadata_list if Path(m["source_data"]["imaging"]["folder_path"]).is_dir()]
# Filter over flies to get only the directories that contain both functional and anatomical imaging
metadata_list = [m for m in metadata_list if "fly" in Path(m["source_data"]["imaging"]["folder_path"]).name]

for index, metadata in enumerate(metadata_list):
    if verbose:
        print("-" * 80)
        print(f"Converting session {index + 1} of {len(metadata_list)}")

    date_string = metadata["metadata"]["extras"]["date_string"]
    subject_id = metadata["metadata"]["Subject"]["subject_id"]
    session_to_nwb(
        data_dir_path=data_dir_path,
        output_dir_path=output_dir_path,
        subject_id=subject_id,
        date_string=date_string,
        stub_test=stub_test,
        verbose=verbose,
    )
