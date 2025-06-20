import os

# Path to the file to be created
file_to_create_str = "/app/prod/lib/test_file_in_lib.txt"

try:
    with open(file_to_create_str, "w") as f:
        f.write("hello from lib")
    print(f"Successfully created file: {file_to_create_str}")
except Exception as e:
    print(f"Error creating file {file_to_create_str}: {e}")

# Verify
if os.path.exists(file_to_create_str):
    print(f"Verification: File {file_to_create_str} exists.")
else:
    print(f"Verification: File {file_to_create_str} does NOT exist.")
