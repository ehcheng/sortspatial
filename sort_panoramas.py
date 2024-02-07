# Copyright (c) 2024 Eric Cheng
# All rights reserved.

# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. 

import os
import subprocess
import shutil

# Define the command line executable path, arguments, and strings to search for in its output
ACCEPTED_EXTENSIONS = ["jpg", "heic", "png"]  # List of accepted file extensions without the dot
EXECUTABLE_PATH = "/opt/homebrew/bin/exiftool"
EXECUTABLE_ARGS = []  # Arguments to be passed to the executable
STRING_MATCH_1 = "Custom Rendered                 : Panorama"
STRING_MATCH_2 = "Custom Rendered                 : Panorama"
FILENAME_KEYWORD = "pano"  # Keyword to check in filename
FILENAME_APPENDIX = "_pano"  # Text to append if keyword is not present

def run_executable_on_file(file_path):
    """Run the executable on the file with specific arguments and return the output, using a specific encoding."""
    try:
        cmd = [EXECUTABLE_PATH] + EXECUTABLE_ARGS + [file_path]
        result = subprocess.run(cmd, capture_output=True, text=False)  # text is set to False to get bytes
        output = result.stdout.decode('ISO-8859-1')  # Change 'ISO-8859-1' to the correct encoding if known
        return output
    except subprocess.CalledProcessError as e:
        print(f"Error running executable on {file_path}: {e}")
        return ""


def check_string_matches(output):
    """Check if the output contains both required string matches."""
    return STRING_MATCH_1 in output and STRING_MATCH_2 in output

def modify_filename_if_needed(file_path):
    """Modify the filename if it doesn't contain the specified keyword."""
    dirname, filename = os.path.split(file_path)
    name, ext = os.path.splitext(filename)
    if FILENAME_KEYWORD not in name:
        new_filename = name + FILENAME_APPENDIX + ext
        return os.path.join(dirname, new_filename)
    return file_path


def copy_file_skip_existing(file_path, output_file_path):
    # Check if the file already exists in the output directory
    if not os.path.exists(output_file_path):
        shutil.copy(file_path, output_file_path)
    else:
        print(f"File {output_file_path} already exists. Skipping.")


def copy_file_to_output(file_path, input_folder, output_folder):
    """Copy the file to the output folder, preserving the folder structure and modifying the filename if needed."""
    # Modify the filename if it doesn't contain the specified keyword
    modified_file_path = modify_filename_if_needed(file_path)
    # Calculate the relative path from the input folder to the modified file path
    relative_path = os.path.relpath(modified_file_path, start=input_folder)
    # Construct the full path for the output file
    output_file_path = os.path.join(output_folder, relative_path)
    # Ensure the directory exists
    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
    # Copy the file
    print("**** MATCH! COPYING TO: ", output_file_path)
    copy_file_skip_existing(file_path, output_file_path)

def process_folder(input_folder, output_folder):
    folders_count = 0
    files_count = 0
    matches_count = 0
    
    for root, dirs, files in os.walk(input_folder):
        folders_count += len(dirs)
        for file in files:
            # Check if the file extension is in the list of accepted extensions
            if file.split('.')[-1].lower() in ACCEPTED_EXTENSIONS:
                files_count += 1
                file_path = os.path.join(root, file)
                # file_path)
                output = run_executable_on_file(file_path)
                if check_string_matches(output):
                    matches_count += 1
                    copy_file_to_output(file_path, input_folder, output_folder)
    
    return folders_count, files_count, matches_count

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: script.py <input_folder> <output_folder>")
        sys.exit(1)
    
    input_folder = sys.argv[1]
    output_folder = sys.argv[2]
    
    folders_analyzed, files_analyzed, matches_copied = process_folder(input_folder, output_folder)
    
    print(f"Folders analyzed: {folders_analyzed}")
    print(f"Files analyzed: {files_analyzed}")
    print(f"Matches copied: {matches_copied}")
