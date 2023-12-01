from pathlib import Path
from clandinin_lab_to_nwb.brezovec.brezovec_convert_session import session_to_nwb

from neuroconv.tools.path_expansion import LocalPathExpander

# Define rooth path and data directory
root_path = Path.home() / "Clandinin-CN-data-share"  # Change this to the directory where the data is stored
root_path = (
    Path("/media/heberto/One Touch/") / "Clandinin-CN-data-share"
)  # Change this to the directory where the data is stored
data_dir_path = root_path / "brezovec_example_data"
output_dir_path = Path.home() / "conversion_nwb"
stub_test = True  # Set to False to convert the full session otherwise only a stub will be converted for testing
verbose = True

# Specify source data (note this assumes the files are arranged in the same way as in the example data)
base_directory = data_dir_path
source_data_spec = {
    "imaging": {
        "base_directory": base_directory,
        "folder_path": "imports/{session_id}/{subject_id}",
    }
}

# Instantiate LocalPathExpander
path_expander = LocalPathExpander()

# Expand paths and extract metadata
metadata_list = path_expander.expand_paths(source_data_spec)

# Filter dor directories that exist and are named "fly" to get the metadata for each session
metadata_list = [
    metadata_match
    for metadata_match in metadata_list
    if Path(metadata_match["source_data"]["imaging"]["folder_path"]).is_dir()
]
metadata_list = [
    metadata_match
    for metadata_match in metadata_list
    if "fly" in Path(metadata_match["source_data"]["imaging"]["folder_path"]).name
]

for metadata in metadata_list:
    session_to_nwb(
        data_dir_path=data_dir_path,
        output_dir_path=output_dir_path,
        subject_id=metadata["metadata"]["Subject"]["subject_id"],
        session_id=metadata["metadata"]["NWBFile"]["session_id"],
        stub_test=stub_test,
        verbose=verbose,
    )
