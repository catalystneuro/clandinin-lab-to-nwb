from pathlib import Path
from clandinin_lab_to_nwb.brezovec.brezovec_convert_session import session_to_nwb

from neuroconv.tools.path_expansion import LocalPathExpander

# Define rooth path and data directory
root_path = Path.home() / "Clandinin-CN-data-share"  # Change this to the directory where the data is stored
data_dir_path = root_path / "brezovec_example_data"
output_dir_path = Path.home() / "conversion_nwb"
stub_test = False  # Set to False to convert the full session otherwise only a stub will be converted for testing
verbose = True

# Specify source data (note this assumes the files are arranged in the same way as in the example data)
source_data_spec = {
    "imaging_function": {
        "base_directory": data_dir_path / "imports",
        "folder_path": "{session_id}/{subject_id}/func_0/TSeries-{session_start_time:%m%d%Y}-{other}/TSeries-{session_start_time:%m%d%Y}-{other}.xml",
    }
}

# Instantiate LocalPathExpander
path_expander = LocalPathExpander()

# Expand paths and extract metadata
metadata_list = path_expander.expand_paths(source_data_spec)

# Print the results
for metadata in metadata_list:
    session_to_nwb(
        data_dir_path=data_dir_path,
        output_dir_path=output_dir_path,
        subject_id=metadata["metadata"]["Subject"]["subject_id"],
        session_id=metadata["metadata"]["NWBFile"]["session_id"],
        stub_test=stub_test,
        verbose=verbose,
    )
