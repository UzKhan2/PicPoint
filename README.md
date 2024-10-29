# PicPoint: Media Sorter

PicPoint is a desktop application designed to organize and sort your images and videos based on their metadata, such as location or creation date. While offering additional features to visualize your files

## Features

### Core Functionality

- **Location-based Sorting**:Organize files into folders based on where they were taken
- **Time-based Sorting**: Sort your files into folders by year and month taken
- **Folder Flattening**: Simplify complex folder structures by moving all files to a single directory
- **Multiple Format Support**: Handles various image and video formats, including HEIC files.
- **Real-time Progress Tracking**: Real-time progress bar and status updates for all operations

### Advanced Features

- **Interactive Maps**: Generate and view location-based maps showing where your media was captured
  - US state-level visualization
  - World country visualization
- **Duplicate Manager**:
  - Find and handle duplicate files
  - Option to move duplicates to separate folders or delete them
  - Intelligent comparison using file size and content hash
- **Metadata Remover**:
  - View detailed metadata information for images and videos
  - Remove metadata from files while preserving image quality
  - Create automatic backups before metadata removal

### TODO

- [ ] Allow you to use arrows to move through images in the metadata preview
- [ ] Make sure videos have an image preview, and full metadata in the preview
- [ ] Allow you to choose another file in the file preview
- [ ] Make sure folder flattening only works on supported files, and not every file
- [ ] Review the possibility of deleting empty folders
- [ ] Review adding setting storage in a txt file
- [ ] Add help button in settings with functionality
- [ ] Add notice to download exiftool to path
- [ ] Review the possibility of screenshots in a separate folder
- [ ] Location sort seems to be far slower, than V1
- [ ] Consider adding time intervals to sort
- [ ] Add file renaming

## Acknowledgments

- OpenStreetMap for providing location data
- ExifTool for metadata handling capabilities
- Various theme designers for color scheme inspiration
