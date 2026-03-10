# sortspatial

Scans folder trees for spatial and immersive media files, then copies matches to an output folder — preserving directory structure and optionally renaming files to indicate their type.

Useful for pulling spatial/immersive content out of large photo libraries or backup drives where these files are mixed in with regular photos and videos.

## Supported media types

| Type | Description | Extensions | Detection method |
|---|---|---|---|
| `spatial-video` | Apple Spatial Videos (stereoscopic MV-HEVC) | `.mov` | Checks for left/right eye streams via `spatial` tool |
| `spatial-photo` | Apple Spatial Photos (stereoscopic HEIC) | `.heic` | Checks for `ster` HEIF box in file header |
| `panorama` | Panoramic photos | `.jpg`, `.heic`, `.png` | Checks EXIF `Custom Rendered: Panorama` |
| `360` | 360° equirectangular photos | `.jpg`, `.heic`, `.png`, `.tif`, `.tiff` | Checks EXIF for `equirectangular` projection |

## Requirements

- Python 3
- [Mike Swanson's Spatial Video Tool](https://blog.mikeswanson.com/spatial) — required for `spatial-video` detection. Install to `~/bin/spatial` (or update `SPATIAL_TOOL_PATH` in script).
- [ExifTool](https://exiftool.org/install.html) — required for `panorama` and `360` detection. Expected at `/opt/homebrew/bin/exiftool` (Homebrew default on Apple Silicon).

`spatial-photo` detection has no external dependencies — it reads the raw HEIC file directly.

## Usage

```
python sort_media.py -t TYPE[,TYPE,...] <input_folder> <output_folder>
```

Scan for specific types:
```bash
python sort_media.py -t spatial-video /Volumes/Photos/2024 /Volumes/Output/spatial
python sort_media.py -t panorama,360 /Volumes/Photos /Volumes/Output/immersive
```

Scan for everything:
```bash
python sort_media.py -t all /Volumes/Backup /Volumes/Sorted
```

## Behavior

- Recursively walks the input folder tree
- Matched files are copied (not moved) to the output folder, preserving the original directory structure
- Files are renamed with a suffix (`_spatial`, `_pano`, `_360`) if the keyword isn't already in the filename
- Existing files in the output folder are skipped
- When multiple types share a file extension (e.g. `.heic`), each file is checked against all relevant types

## License

BSD — see [LICENSE](LICENSE).
