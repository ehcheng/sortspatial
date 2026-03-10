#!/usr/bin/env python3

# Copyright (c) 2024 Eric Cheng
# All rights reserved.

# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

# External tool requirements:
#   spatial-video: Mike Swanson's Spatial Video Tool (https://blog.mikeswanson.com/spatial)
#   panorama, 360: ExifTool (https://exiftool.org/install.html)
#   spatial-photo: No external tool needed (checks for HEIF "ster" box in raw file)

import argparse
import os
import subprocess
import shutil
import sys

EXIFTOOL_PATH = "/opt/homebrew/bin/exiftool"
SPATIAL_TOOL_PATH = "/Users/echeng/bin/spatial"

# Bytes to read when checking for the HEIF "ster" stereo box.
# The ster box is in the meta/iref area, typically within the first 32KB.
HEIF_HEADER_READ_SIZE = 32768


def has_heif_ster_box(file_path):
    """Check if a HEIC file contains a 'ster' HEIF box, indicating a spatial (stereo) photo."""
    try:
        with open(file_path, "rb") as f:
            header = f.read(HEIF_HEADER_READ_SIZE)
        return b"ster" in header
    except OSError:
        return False


MEDIA_TYPES = {
    "spatial-video": {
        "description": "Apple Spatial Videos (stereoscopic MV-HEVC)",
        "extensions": ["mov"],
        "executable": SPATIAL_TOOL_PATH,
        "args": ["info", "--input"],
        "match_strings": ["Has left eye", "Has right eye"],
        "filename_keyword": "spatial",
        "filename_appendix": "_spatial",
    },
    "spatial-photo": {
        "description": "Apple Spatial Photos (stereoscopic HEIC)",
        "extensions": ["heic"],
        # Uses custom detection (has_heif_ster_box) instead of an external tool.
        "custom_check": has_heif_ster_box,
        "filename_keyword": "spatial",
        "filename_appendix": "_spatial",
    },
    "panorama": {
        "description": "Panoramic photos",
        "extensions": ["jpg", "heic", "png"],
        "executable": EXIFTOOL_PATH,
        "args": [],
        "match_strings": ["Custom Rendered                 : Panorama"],
        "filename_keyword": "pano",
        "filename_appendix": "_pano",
    },
    "360": {
        "description": "360° equirectangular photos",
        "extensions": ["jpg", "heic", "png", "tif", "tiff"],
        "executable": EXIFTOOL_PATH,
        "args": [],
        "match_strings": ["equirectangular"],
        "filename_keyword": "_360",
        "filename_appendix": "_360",
    },
}


def run_tool(executable, args, file_path):
    """Run an external tool on a file and return its stdout."""
    try:
        cmd = [executable] + args + [file_path]
        result = subprocess.run(cmd, capture_output=True, text=False)
        return result.stdout.decode("ISO-8859-1")
    except subprocess.CalledProcessError as e:
        print(f"Error running {executable} on {file_path}: {e}")
        return ""


def check_matches(output, match_strings):
    """Check if output contains all required match strings."""
    return all(s in output for s in match_strings)


def modify_filename_if_needed(file_path, keyword, appendix):
    """Append keyword suffix to filename if not already present."""
    dirname, filename = os.path.split(file_path)
    name, ext = os.path.splitext(filename)
    if keyword not in name:
        return os.path.join(dirname, name + appendix + ext)
    return file_path


def copy_file_skip_existing(src, dst):
    """Copy file, skipping if destination already exists."""
    if not os.path.exists(dst):
        shutil.copy(src, dst)
    else:
        print(f"File {dst} already exists. Skipping.")


def copy_file_to_output(file_path, input_folder, output_folder, keyword, appendix):
    """Copy file to output folder, preserving directory structure and renaming if needed."""
    modified_path = modify_filename_if_needed(file_path, keyword, appendix)
    relative_path = os.path.relpath(modified_path, start=input_folder)
    output_path = os.path.join(output_folder, relative_path)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    print(f"**** MATCH! COPYING TO: {output_path}")
    copy_file_skip_existing(file_path, output_path)


def process_folder(input_folder, output_folder, configs):
    """Walk input folder and process files against all selected media type configs."""
    # Build a combined extension-to-configs mapping so each file is checked
    # against all relevant media types and we only call each unique tool once.
    ext_configs = {}
    for config in configs:
        for ext in config["extensions"]:
            ext_configs.setdefault(ext, []).append(config)

    all_extensions = set(ext_configs.keys())
    folders_count = 0
    files_count = 0
    matches_by_type = {c["description"]: 0 for c in configs}

    for root, dirs, files in os.walk(input_folder):
        folders_count += len(dirs)
        for file in files:
            ext = file.rsplit(".", 1)[-1].lower() if "." in file else ""
            if ext not in all_extensions:
                continue

            files_count += 1
            file_path = os.path.join(root, file)

            # Group configs by (executable, args_tuple) to avoid redundant tool calls
            tool_cache = {}
            for config in ext_configs[ext]:
                # Use custom check function if provided, otherwise shell out
                if "custom_check" in config:
                    matched = config["custom_check"](file_path)
                else:
                    tool_key = (config["executable"], tuple(config["args"]))
                    if tool_key not in tool_cache:
                        tool_cache[tool_key] = run_tool(
                            config["executable"], config["args"], file_path
                        )
                    matched = check_matches(
                        tool_cache[tool_key], config["match_strings"]
                    )

                if matched:
                    matches_by_type[config["description"]] += 1
                    copy_file_to_output(
                        file_path,
                        input_folder,
                        output_folder,
                        config["filename_keyword"],
                        config["filename_appendix"],
                    )

    return folders_count, files_count, matches_by_type


def build_type_table():
    """Build a formatted table describing all available media types."""
    lines = []
    for name, cfg in MEDIA_TYPES.items():
        exts = ", ".join(f".{e}" for e in cfg["extensions"])
        if "custom_check" in cfg:
            tool = "built-in (HEIF ster box check)"
        else:
            tool = os.path.basename(cfg["executable"])
        lines.append(f"  {name:<16} {cfg['description']}")
        lines.append(f"  {'':<16} Extensions: {exts}")
        lines.append(f"  {'':<16} Requires:   {tool}")
        lines.append(f"  {'':<16} Renames:    adds '{cfg['filename_appendix']}' if '{cfg['filename_keyword']}' not in filename")
        lines.append("")
    return "\n".join(lines)


EPILOG = f"""\
available media types:
{build_type_table()}\
examples:
  %(prog)s -t spatial-video /Volumes/Photos/2024 /Volumes/Output/spatial
  %(prog)s -t panorama,360 /Volumes/Photos /Volumes/Output/immersive
  %(prog)s -t all /Volumes/Backup /Volumes/Sorted
"""


def main():
    type_names = list(MEDIA_TYPES.keys())
    parser = argparse.ArgumentParser(
        description="Scan a folder tree for spatial/immersive media and copy matches to an output folder, "
        "preserving directory structure.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-t",
        "--type",
        required=True,
        metavar="TYPE",
        help="comma-separated media types to detect, or 'all'",
    )
    parser.add_argument("input_folder", help="root folder to scan recursively")
    parser.add_argument("output_folder", help="destination folder for matched files (created if needed)")
    args = parser.parse_args()

    # Parse requested types
    if args.type == "all":
        selected = type_names
    else:
        selected = [t.strip() for t in args.type.split(",")]
        invalid = [t for t in selected if t not in MEDIA_TYPES]
        if invalid:
            parser.error(
                f"Unknown type(s): {', '.join(invalid)}. "
                f"Valid types: {', '.join(type_names)}, all"
            )

    configs = [MEDIA_TYPES[t] for t in selected]
    print(f"Scanning for: {', '.join(selected)}")
    print(f"Input:  {args.input_folder}")
    print(f"Output: {args.output_folder}\n")

    folders, files, matches = process_folder(
        args.input_folder, args.output_folder, configs
    )

    print(f"\nFolders analyzed: {folders}")
    print(f"Files analyzed: {files}")
    for desc, count in matches.items():
        print(f"  {desc}: {count} matched")


if __name__ == "__main__":
    main()
