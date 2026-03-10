# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Unified Python CLI tool (`sort_media.py`) that scans folder trees for specific spatial/immersive media types using external CLI tools, then copies matching files to an output folder (preserving directory structure and optionally renaming).

Legacy per-type scripts (`sort_spatial_videos.py`, `sort_panoramas.py`, `sort_360.py`) are in `legacy/`.

## Running

```bash
python sort_media.py -t <type>[,<type>...] <input_folder> <output_folder>
python sort_media.py -t all <input_folder> <output_folder>
```

Valid types: `spatial-video`, `spatial-photo`, `panorama`, `360`

No dependencies beyond Python 3 stdlib — but the tool shells out to external tools:

| Media Type | External Tool | Install |
|---|---|---|
| `spatial-video` | Mike Swanson's `spatial` (`~/bin/spatial`) | https://blog.mikeswanson.com/spatial |
| `panorama`, `360` | ExifTool (`/opt/homebrew/bin/exiftool`) | https://exiftool.org/install.html |
| `spatial-photo` | None (reads raw HEIF bytes) | — |

## Architecture

`sort_media.py` uses a data-driven design: the `MEDIA_TYPES` dict at the top of the file defines each media type's config (extensions, detection method, filename keyword/appendix). All processing logic is shared.

Key design choices:
- Most types detect via shelling out to an external tool and matching strings in the output
- `spatial-photo` uses a `custom_check` function instead — reads the first 32KB of the HEIC and looks for the `ster` HEIF box (Apple's stereo pair marker), since exiftool doesn't expose this
- When multiple types share an extension (e.g. `.heic` for both `spatial-photo` and `panorama`), each file is checked against all relevant types
- Tool output is cached per unique (executable, args) combo to avoid redundant subprocess calls on the same file
- Files are renamed with a suffix (e.g. `_spatial`, `_pano`, `_360`) if the keyword isn't already in the filename

## Detection Logic

- **spatial-video**: `spatial info` output contains `"Has left eye"` and `"Has right eye"` (`.mov`)
- **spatial-photo**: raw HEIC file contains `ster` HEIF box in first 32KB (`.heic`)
- **panorama**: exiftool output contains `"Custom Rendered                 : Panorama"` (`.jpg/.heic/.png`)
- **360**: exiftool output contains `"equirectangular"` (`.jpg/.heic/.png/.tif/.tiff`)
