from constants import (IMAGE_FORMATS, VIDEO_FORMATS, SUPPORTED_MEDIA_FORMATS, STATE_MAPPING, 
                       COUNTRY_MAPPING, COUNTRY_CODES)
from utils import (extract_gps_info_image, extract_gps_info_video, 
                   get_location_from_coordinates, move_to_folder, get_creation_time, 
                   check_internet_connection)
from PyQt5.QtCore import QThread, pyqtSignal
import requests
import shutil
import time
import re
import os

class MapGenerationThread(QThread):
    update_progress = pyqtSignal(int)
    update_output = pyqtSignal(str)
    finished = pyqtSignal(list, list, str, str)
    internet_check_failed = pyqtSignal()

    def __init__(self, folder_path, us_svg_path, world_svg_path):
        super().__init__()
        self.folder_path = folder_path
        self.us_svg_path = us_svg_path
        self.world_svg_path = world_svg_path
        self.state_cache = {}
        self.country_cache = {}

    def normalize_country_name(self, country):
        """Normalize country names to English"""
        return COUNTRY_MAPPING.get(country, country)
    
    def get_location_details(self, lat, lon):
        """Get both country and state information for coordinates"""
        cache_key = f"{lat},{lon}"
        
        if cache_key in self.state_cache:
            return self.state_cache[cache_key]
            
        base_url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            "lat": lat,
            "lon": lon,
            "format": "json"
        }
        headers = {
            "User-Agent": "Media GPS Extractor/1.0"
        }
        
        try:
            response = requests.get(base_url, params=params, headers=headers)
            if response.status_code == 200:
                data = response.json()
                address = data.get('address', {})
                country = self.normalize_country_name(address.get('country', 'Unknown'))
                state = None
                
                if address.get('country_code', '').upper() == 'US':
                    state = address.get('state', None)
                    country = "United States"
                
                result = {'country': country, 'state': state}
                self.state_cache[cache_key] = result
                return result
            else:
                return None
        except Exception as e:
            self.update_output.emit(f"Error fetching location: {str(e)}")
            return None
        
    def get_all_files(self):
        """Get all files from the specified folder"""
        all_files = []
        for file in os.listdir(self.folder_path):
            file_path = os.path.join(self.folder_path, file)
            if os.path.isfile(file_path):
                all_files.append(file_path)
        return all_files

    def update_svg_maps(self, us_states, world_countries):
        # Update United States map
        us_svg = None
        if os.path.exists(self.us_svg_path):
            try:
                with open(self.us_svg_path, 'r', encoding='utf-8') as f:
                    us_svg = f.read()
                    for state in us_states:
                        state_abbr = self.get_state_abbreviation(state)
                        if state_abbr:
                            pattern = f'(<path[^>]*id="{state_abbr}"[^>]*style=")[^"]*(")'
                            replacement = r'\1stroke-width:0.97063118000000004;fill:#2ecc71\2'
                            us_svg = re.sub(pattern, replacement, us_svg)

            except Exception as e:
                self.update_output.emit(f"Error updating US map: {str(e)}")

        # Update World map
        world_svg = None
        if os.path.exists(self.world_svg_path):
            try:
                with open(self.world_svg_path, 'r', encoding='utf-8') as f:
                    world_svg = f.read()
                    
                    for country in world_countries:
                        country_code = self.get_country_code(country)
                        if country_code:
                                id_pattern = f'(<path[^>]*id="{country_code}"[^>]*)'
                                if re.search(id_pattern, world_svg):
                                    style_pattern = f'(<path[^>]*id="{country_code}"[^>]*style=")[^"]*(")'
                                    if re.search(style_pattern, world_svg):
                                        replacement = r'\1stroke-width:0.97063118000000004;fill:#2ecc71\2'
                                        world_svg = re.sub(style_pattern, replacement, world_svg)
                                    else:
                                        replacement = r'\1 style="fill:#2ecc71;stroke-width:0.97063118000000004"'
                                        world_svg = re.sub(id_pattern, replacement, world_svg)

            except Exception as e:
                self.update_output.emit(f"Error updating world map: {str(e)}")

        return us_svg, world_svg

    def get_state_abbreviation(self, state_name):
        """Convert state name to abbreviation"""
        return STATE_MAPPING.get(state_name)

    def get_country_code(self, country_name):
        """Convert country name to code used in SVG"""
        return COUNTRY_CODES.get(country_name, country_name)
    
    def run(self):
        try:
            all_files = self.get_all_files()
            total_files = len(all_files)
            us_states = set()
            world_countries = set()

            if total_files == 0:
                self.finished.emit([], [], "", "")
                return

            self.update_output.emit("Checking internet connection...")
            time.sleep(0.5)
            
            if not check_internet_connection():
                self.update_output.emit("Error: No internet connection. Map generation requires internet access.")
                self.internet_check_failed.emit()
                return

            for index, file_path in enumerate(all_files, 1):
                try:
                    file_extension = os.path.splitext(file_path)[1].lower()
                    coordinates = None

                    if file_extension in IMAGE_FORMATS:
                        coordinates = extract_gps_info_image(file_path)
                    elif file_extension in VIDEO_FORMATS:
                        coordinates = extract_gps_info_video(file_path)

                    if coordinates:
                        lat, lon = coordinates
                        location = self.get_location_details(lat, lon)
                        if location:
                            country = location['country']
                            if location['state']:
                                us_states.add(location['state'])
                                world_countries.add('United States')
                                self.update_output.emit(f"Found location in {location['state']}, United States")
                            else:
                                world_countries.add(country)
                                self.update_output.emit(f"Found location in {country}")
                    
                    progress = int((index / total_files) * 100)
                    self.update_progress.emit(progress)
                    
                except Exception as e:
                    self.update_output.emit(f"Error processing file: {str(e)}")

            us_states_list = sorted(list(us_states))
            world_countries_list = sorted(list(world_countries))

            if not us_states_list and not world_countries_list:
                self.finished.emit([], [], "", "")
                return

            self.update_output.emit("\nLocations found in media files:")
            if us_states_list:
                self.update_output.emit("\nUS States:")
                for state in us_states_list:
                    self.update_output.emit(f"- {state}")
            if world_countries_list:
                self.update_output.emit("\nCountries:")
                for country in world_countries_list:
                    self.update_output.emit(f"- {country}")

            us_svg, world_svg = self.update_svg_maps(us_states_list, world_countries_list)
            self.finished.emit(us_states_list, world_countries_list, us_svg, world_svg)

        except Exception as e:
            self.update_output.emit(f"Error during map generation: {str(e)}")
            self.finished.emit([], [], "", "")
            
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
                self.update_output.emit("Error: No internet connection. Location sorting requires internet access.")
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

    def get_unique_filename(self, dest_folder, filename):
        """Generate a unique filename if the file already exists."""
        base_name, ext = os.path.splitext(filename)
        counter = 1
        new_filename = filename
        
        while os.path.exists(os.path.join(dest_folder, new_filename)):
            new_filename = f"{base_name} ({counter}){ext}"
            counter += 1
            
        return new_filename

    def run(self):
        try:
            all_files = self.get_all_files()
            total_files = len(all_files)
            
            if total_files == 0:
                self.update_output.emit("No files found to flatten")
                self.finished.emit()
                return
            
            for index, src_path in enumerate(all_files, 1):
                try:
                    file_name = os.path.basename(src_path)
                    # Generate unique filename
                    unique_name = self.get_unique_filename(self.folder_path, file_name)
                    dest_path = os.path.join(self.folder_path, unique_name)
                    
                    shutil.move(src_path, dest_path)
                    
                    progress = int((index / total_files) * 100)
                    self.update_progress.emit(progress)
                    
                    if file_name != unique_name:
                        self.update_output.emit(f"Moved: {file_name} → {unique_name} ({index}/{total_files})")
                    else:
                        self.update_output.emit(f"Moved: {file_name} ({index}/{total_files})")
                        
                except Exception as e:
                    self.update_output.emit(f"Error moving {file_name}: {str(e)}")
                    
            # Clean up empty directories
            for root, dirs, files in os.walk(self.folder_path, topdown=False):
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    try:
                        if not os.listdir(dir_path):
                            os.rmdir(dir_path)
                    except Exception as e:
                        self.update_output.emit(f"Error removing empty directory {dir_name}: {str(e)}")
            
            self.update_output.emit("\nFolder flattening completed")

        except Exception as e:
            self.update_output.emit(f"Error during flattening: {str(e)}")
        finally:
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