from PyQt5.QtCore import QThread, pyqtSignal
from utils import (extract_gps_info_image, extract_gps_info_video, 
                   get_location_from_coordinates, move_to_folder, get_creation_time)
from constants import IMAGE_FORMATS, VIDEO_FORMATS, SUPPORTED_MEDIA_FORMATS
import os
import glob
import shutil

class SortByLocThread(QThread):
    update_progress = pyqtSignal(int)
    update_output = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, folder_path):
        super().__init__()
        self.folder_path = folder_path
        self.total_files = 0
        self.processed_files = 0

    def run(self):
        unsupported_formats = set()
        
        # Count total files including those in subfolders
        for root, _, files in os.walk(self.folder_path):
            self.total_files += len(files)

        if self.total_files == 0:
            self.update_output.emit("No files found to sort")
            self.finished.emit()
            return

        for root, _, files in os.walk(self.folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                file_extension = os.path.splitext(file_path)[1].lower()
                
                if file_extension in SUPPORTED_MEDIA_FORMATS:
                    self.process_media(file_path)
                else:
                    self.update_output.emit(f"Unsupported file: {file}")
                    move_to_folder(file_path, 'Not Supported')
                    unsupported_formats.add(file_extension)
                
                self.processed_files += 1
                progress = int((self.processed_files / self.total_files) * 100)
                self.update_progress.emit(progress)
                self.update_output.emit(f"Processed: {file} ({self.processed_files}/{self.total_files})")

        if unsupported_formats:
            unsupported_str = "\nUnsupported file formats encountered:\n"
            unsupported_str += "\n".join([f"- {format}" for format in unsupported_formats])
            self.update_output.emit(unsupported_str)

        self.finished.emit()

    def process_media(self, file_path):
        file_name = os.path.basename(file_path)
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension in IMAGE_FORMATS:
            coordinates = extract_gps_info_image(file_path)
        elif file_extension in VIDEO_FORMATS:
            coordinates = extract_gps_info_video(file_path)
        else:
            self.update_output.emit(f"Unsupported file: {file_name}")
            move_to_folder(file_path, 'Not Supported')
            return

        if coordinates:
            lat, lon = coordinates
            self.update_output.emit(f"File: {file_name}")
            self.update_output.emit(f"GPS Coordinates: {lat}, {lon}")
            
            city = get_location_from_coordinates(lat, lon)
            self.update_output.emit(f"City: {city}")
            
            move_to_folder(file_path, city)
            self.update_output.emit(f"Moved {file_name} to {city}")
        else:
            self.update_output.emit(f"No location information found for {file_name}")
            move_to_folder(file_path, 'Unknown')
            self.update_output.emit(f"Moved {file_name} to Unknown")
        self.update_output.emit("")

class FlattenFolderThread(QThread):
    update_progress = pyqtSignal(int)
    update_output = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, folder_path):
        super().__init__()
        self.folder_path = folder_path
        self.total_files = 0
        self.processed_files = 0

    def run(self):
        file_counts = {}
        
        # Count total files including those in subfolders
        for root, _, files in os.walk(self.folder_path):
            self.total_files += len(files)

        if self.total_files == 0:
            self.update_output.emit("No files found to flatten")
            self.finished.emit()
            return

        for root, _, files in os.walk(self.folder_path):
            for file in files:
                src_path = os.path.join(root, file)
                
                if file in file_counts:
                    file_counts[file] += 1
                    base_name, ext = os.path.splitext(file)
                    new_file = f"{base_name} {file_counts[file]}{ext}"
                    dest_path = os.path.join(self.folder_path, new_file)
                else:
                    file_counts[file] = 0
                    dest_path = os.path.join(self.folder_path, file.replace('_', ' '))
                
                shutil.move(src_path, dest_path)
                self.processed_files += 1
                progress = int((self.processed_files / self.total_files) * 100)
                self.update_progress.emit(progress)
                self.update_output.emit(f"Moved: {file} ({self.processed_files}/{self.total_files})")

        self.finished.emit()

class SortByTimeThread(QThread):
    update_progress = pyqtSignal(int)
    update_output = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, folder_path):
        super().__init__()
        self.folder_path = folder_path
        self.total_files = 0
        self.processed_files = 0

    def run(self):
        # Count total files including those in subfolders
        for root, _, files in os.walk(self.folder_path):
            self.total_files += len(files)

        if self.total_files == 0:
            self.update_output.emit("No files found to sort")
            self.finished.emit()
            return

        for root, _, files in os.walk(self.folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    date = get_creation_time(file_path)
                    
                    year_month = date.strftime("%b, %y")
                    new_folder = os.path.join(self.folder_path, year_month)
                    if not os.path.exists(new_folder):
                        os.makedirs(new_folder)
                    
                    new_file_path = os.path.join(new_folder, file)
                    shutil.move(file_path, new_file_path)
                    
                    self.processed_files += 1
                    progress = int((self.processed_files / self.total_files) * 100)
                    self.update_progress.emit(progress)
                    self.update_output.emit(f"Moved {file} to {year_month} ({self.processed_files}/{self.total_files})")
                except Exception as e:
                    self.update_output.emit(f"Error processing {file}: {str(e)}")
                    self.processed_files += 1

        self.finished.emit()
