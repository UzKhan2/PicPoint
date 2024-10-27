from PyQt5.QtCore import QThread, pyqtSignal
from utils import (extract_gps_info_image, extract_gps_info_video, 
                   get_location_from_coordinates, move_to_folder, get_creation_time,
                   check_internet_connection)
from constants import IMAGE_FORMATS, VIDEO_FORMATS, SUPPORTED_MEDIA_FORMATS
import os
import shutil
import time

class SortByLocThread(QThread):
    update_progress = pyqtSignal(int)
    update_output = pyqtSignal(str)
    finished = pyqtSignal()
    file_processed = pyqtSignal()
    internet_check_failed = pyqtSignal()

    def __init__(self, folder_path, is_additional_sort=False):
        super().__init__()
        self.folder_path = folder_path
        self.is_additional_sort = is_additional_sort

    def get_all_files(self):
        all_files = []
        try:
            if self.is_additional_sort:
                # For additional sorting, process files in all immediate subdirectories
                for item in os.listdir(self.folder_path):
                    item_path = os.path.join(self.folder_path, item)
                    if os.path.isdir(item_path):
                        for file in os.listdir(item_path):
                            file_path = os.path.join(item_path, file)
                            if os.path.isfile(file_path):
                                all_files.append(file_path)
            else:
                # For initial sorting, only process files in the selected directory
                for file in os.listdir(self.folder_path):
                    file_path = os.path.join(self.folder_path, file)
                    if os.path.isfile(file_path):
                        all_files.append(file_path)
        except Exception as e:
            self.update_output.emit(f"Error accessing directory: {str(e)}")
        return all_files

    def run(self):
        try:
            unsupported_formats = set()
            all_files = self.get_all_files()
            total_files = len(all_files)

            if total_files == 0:
                self.update_output.emit("No files found to sort")
                self.update_output.emit("Location sorting completed")
                self.finished.emit()
                return

            self.update_output.emit("Checking internet connection...")
            time.sleep(0.5)  # Small delay to ensure message is visible
            
            if not check_internet_connection():
                self.update_output.emit("Error: No internet connection. Location sorting requires internet access to identify locations.")
                self.internet_check_failed.emit()
                self.finished.emit()
                return

            for index, file_path in enumerate(all_files, 1):
                try:
                    file_name = os.path.basename(file_path)
                    file_extension = os.path.splitext(file_path)[1].lower()

                    if file_extension in SUPPORTED_MEDIA_FORMATS:
                        self.process_media(file_path, file_name, index, total_files)
                        self.file_processed.emit()
                    else:
                        self.update_output.emit(f"Moved {file_name} to Not Supported ({index}/{total_files})")
                        move_to_folder(file_path, 'Not Supported')
                        unsupported_formats.add(file_extension)
                        self.file_processed.emit()

                    progress = int((index / total_files) * 100)
                    self.update_progress.emit(progress)
                except Exception as e:
                    self.update_output.emit(f"Error processing {file_name}: {str(e)}")

            if unsupported_formats:
                unsupported_str = "\nUnsupported file formats encountered:\n"
                unsupported_str += "\n".join([f"- {format}" for format in unsupported_formats])
                self.update_output.emit(unsupported_str)

            self.update_output.emit("Location sorting completed")

        except Exception as e:
            self.update_output.emit(f"Error during sorting: {str(e)}")
        finally:
            self.finished.emit()

    def process_media(self, file_path, file_name, index, total_files):
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension in IMAGE_FORMATS:
            coordinates = extract_gps_info_image(file_path)
        elif file_extension in VIDEO_FORMATS:
            coordinates = extract_gps_info_video(file_path)
        else:
            move_to_folder(file_path, 'Not Supported')
            self.update_output.emit(f"Moved {file_name} to Not Supported ({index}/{total_files})")
            return

        if coordinates:
            lat, lon = coordinates
            city = get_location_from_coordinates(lat, lon)
            move_to_folder(file_path, city)
            self.update_output.emit(f"Moved {file_name} to {city} ({index}/{total_files})")
        else:
            move_to_folder(file_path, 'Unknown')
            self.update_output.emit(f"Moved {file_name} to Unknown ({index}/{total_files})")

class FlattenFolderThread(QThread):
    update_progress = pyqtSignal(int)
    update_output = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, folder_path):
        super().__init__()
        self.folder_path = folder_path

    def get_all_files(self):
        all_files = []
        for root, _, files in os.walk(self.folder_path):
            if root == self.folder_path:  # Skip files already in root folder
                continue
            for file in files:
                file_path = os.path.join(root, file)
                all_files.append(file_path)
        return all_files

    def run(self):
        all_files = self.get_all_files()
        total_files = len(all_files)
        file_counts = {}

        if total_files == 0:
            self.update_output.emit("No files found to flatten")
            self.finished.emit()
            return

        for index, src_path in enumerate(all_files, 1):
            file_name = os.path.basename(src_path)
            
            if file_name in file_counts:
                file_counts[file_name] += 1
                base_name, ext = os.path.splitext(file_name)
                new_file = f"{base_name} {file_counts[file_name]}{ext}"
                dest_path = os.path.join(self.folder_path, new_file)
            else:
                file_counts[file_name] = 0
                dest_path = os.path.join(self.folder_path, file_name.replace('_', ' '))
            
            shutil.move(src_path, dest_path)
            progress = int((index / total_files) * 100)
            self.update_progress.emit(progress)
            self.update_output.emit(f"Moved: {file_name} ({index}/{total_files})")

        self.finished.emit()

class SortByTimeThread(QThread):
    update_progress = pyqtSignal(int)
    update_output = pyqtSignal(str)
    finished = pyqtSignal()
    file_processed = pyqtSignal()

    def __init__(self, folder_path, is_additional_sort=False):
        super().__init__()
        self.folder_path = folder_path
        self.is_additional_sort = is_additional_sort

    def get_all_files(self):
        all_files = []
        if self.is_additional_sort:
            # For additional sorting, process files in all immediate subdirectories
            for item in os.listdir(self.folder_path):
                item_path = os.path.join(self.folder_path, item)
                if os.path.isdir(item_path):
                    for file in os.listdir(item_path):
                        file_path = os.path.join(item_path, file)
                        if os.path.isfile(file_path):
                            all_files.append(file_path)
        else:
            # For initial sorting, only process files in the selected directory
            for file in os.listdir(self.folder_path):
                file_path = os.path.join(self.folder_path, file)
                if os.path.isfile(file_path):
                    all_files.append(file_path)
        return all_files

    def run(self):
        try:
            all_files = self.get_all_files()
            total_files = len(all_files)

            if total_files == 0:
                self.update_output.emit("No files found to sort")
                self.update_output.emit("Time sorting completed")
                self.finished.emit()
                return

            for index, file_path in enumerate(all_files, 1):
                try:
                    file_name = os.path.basename(file_path)
                    date = get_creation_time(file_path)
                    year_month = date.strftime("%b, %y")
                    
                    if self.is_additional_sort:
                        parent_folder = os.path.dirname(file_path)
                        new_folder = os.path.join(parent_folder, year_month)
                    else:
                        new_folder = os.path.join(self.folder_path, year_month)
                    
                    if not os.path.exists(new_folder):
                        os.makedirs(new_folder)
                    
                    new_file_path = os.path.join(new_folder, file_name)
                    shutil.move(file_path, new_file_path)
                    
                    progress = int((index / total_files) * 100)
                    self.update_progress.emit(progress)
                    self.update_output.emit(f"Moved {file_name} to {year_month} ({index}/{total_files})")
                    self.file_processed.emit()
                    
                except Exception as e:
                    self.update_output.emit(f"Error processing {file_name}: {str(e)}")

            if total_files > 0:
                self.update_output.emit("Time sorting completed")
                    
        except Exception as e:
            self.update_output.emit(f"Error during sorting: {str(e)}")
        finally:
            self.finished.emit()