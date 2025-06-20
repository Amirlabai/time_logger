import os
from pathlib import Path

# Path to the directory to be created
# Hardcode for simplicity, avoiding config import
dir_to_create_str = "/app/prod/lib/testDir" # Changed directory name

try:
    os.makedirs(dir_to_create_str, exist_ok=True)
    print(f"Successfully created or ensured directory: {dir_to_create_str}")
except Exception as e:
    print(f"Error creating directory {dir_to_create_str}: {e}")

# Verify
if os.path.exists(dir_to_create_str):
    print(f"Verification: Directory {dir_to_create_str} exists.")
    # Try creating a file inside it
    test_file_path = os.path.join(dir_to_create_str, "test.txt")
    with open(test_file_path, "w") as f:
        f.write("hello")
    if os.path.exists(test_file_path):
        print(f"Verification: File {test_file_path} created.")
    else:
        print(f"Verification: Failed to create file in {dir_to_create_str}.")
else:
    print(f"Verification: Directory {dir_to_create_str} does NOT exist.")
