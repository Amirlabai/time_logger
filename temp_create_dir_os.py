import os
from pathlib import Path
import prod.code.config as config # To get DB_PATH

# Path to the directory to be created
# Convert Path object to string for os.makedirs
dir_to_create_str = str(config.DB_PATH.parent)

try:
    # exist_ok=True is the default behavior if the directory already exists with os.makedirs
    os.makedirs(dir_to_create_str, exist_ok=True)
    print(f"Successfully created or ensured directory: {dir_to_create_str}")
except Exception as e:
    print(f"Error creating directory {dir_to_create_str}: {e}")

# Also check if the user_programs.json exists, just for sanity
user_programs_file_str = str(config.USER_PROGRAMS_FILE_PATH)
if os.path.exists(user_programs_file_str):
    print(f"Checked: {user_programs_file_str} exists.")
else:
    print(f"Checked: {user_programs_file_str} DOES NOT exist.")
