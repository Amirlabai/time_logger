from pathlib import Path
import prod.code.config as config # To get DB_PATH

# Path to the directory to be created
dir_to_create = config.DB_PATH.parent

try:
    dir_to_create.mkdir(parents=True, exist_ok=True)
    print(f"Successfully created or ensured directory: {dir_to_create}")
except Exception as e:
    print(f"Error creating directory {dir_to_create}: {e}")

# Also check if the user_programs.json exists, just for sanity
user_programs_file = config.USER_PROGRAMS_FILE_PATH
if user_programs_file.exists():
    print(f"Checked: {user_programs_file} exists.")
else:
    print(f"Checked: {user_programs_file} DOES NOT exist.")
