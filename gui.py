from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, 
    QProgressBar, QTextEdit, QLabel, QLineEdit, QFrame, QScrollArea, QDesktopWidget, 
    QDialog, QStackedLayout, QMessageBox, QMenu
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QSize, QPoint, QUrl, QThread, pyqtSignal
from workers import SortByLocThread, FlattenFolderThread, SortByTimeThread, MapGenerationThread
from constants import IMAGE_FORMATS, VIDEO_FORMATS, SUPPORTED_MEDIA_FORMATS
from PyQt5.QtGui import QFont, QIcon, QImage, QPainter, QColor, QPixmap
from PyQt5.QtWebEngineWidgets import QWebEngineView
from theme_manager import ThemeManager
from typing import Dict, List, Tuple
from PIL import Image
import tempfile
import exiftool
import hashlib
import piexif
import shutil
import os

class PostSortDialog(QDialog):
    def __init__(self, parent=None, sort_type="location"):
        super().__init__(parent)
        self.sort_type = sort_type
        self.result = None
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("PicPoint")
        self.setWindowIcon(QIcon('assets/icons/app_icon.png'))
        
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        self.setFixedSize(400, 200)
        
        layout = QVBoxLayout()
        
        # Pop-up Message
        title = "Additional Sorting Options"
        message = (f"Would you like to further sort these files by "
                  f"{'date' if self.sort_type == 'location' else 'location'}?")
        
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        message_label = QLabel(message)
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setWordWrap(True)
        
        button_layout = QHBoxLayout()
        yes_button = QPushButton("Yes")
        no_button = QPushButton("No")
        
        yes_button.setFixedSize(100, 40)
        no_button.setFixedSize(100, 40)
        
        yes_button.clicked.connect(self.accept_sort)
        no_button.clicked.connect(self.reject_sort)
        
        button_layout.addWidget(yes_button)
        button_layout.addWidget(no_button)
        
        layout.addSpacing(20)
        layout.addWidget(title_label)
        layout.addSpacing(10)
        layout.addWidget(message_label)
        layout.addSpacing(20)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Apply theme
        self.apply_theme_colors(self.parent().current_theme)
    
    def accept_sort(self):
        self.result = True
        self.accept()
    
    def reject_sort(self):
        self.result = False
        self.reject()
    
    def apply_theme_colors(self, colors):
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {colors['card_bg']};
            }}
            QLabel {{
                color: {colors['text']};
                font-size: 14px;
            }}
            QPushButton {{
                background-color: {colors['button_bg']};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {colors['button_hover']};
            }}
        """)

class ThemeButton(QPushButton):
    def __init__(self, theme_name, theme_data, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(180, 60)
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 5, 10, 5)
        main_layout.setSpacing(10)
        
        self.color_preview = QWidget(self)
        self.color_preview.setFixedSize(30, 30)
        self.color_preview.setStyleSheet(f"""
            background-color: {theme_data['colors']['button_bg']};
            border-radius: 15px;
        """)
        main_layout.addWidget(self.color_preview)
        
        self.name_label = QLabel(theme_name, self)
        self.name_label.setStyleSheet(f"""
            color: {theme_data['colors']['text']};
            font-size: 14px;
        """)
        main_layout.addWidget(self.name_label)
        
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme_data['colors']['card_bg']};
                border: 2px solid {theme_data['colors']['button_bg']};
                border-radius: 5px;
                text-align: left;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: {theme_data['colors']['button_hover']}40;
            }}
        """)

    def update_theme_colors(self, colors):
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['card_bg']};
                border: 2px solid {colors['button_bg']};
                border-radius: 5px;
                text-align: left;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: {colors['button_hover']}40;
            }}
        """)
        self.name_label.setStyleSheet(f"""
            color: {colors['text']};
            font-size: 14px;
        """)

class CardWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")

class ModernButton(QPushButton):
    def __init__(self, text, icon_path=None, parent=None):
        super().__init__(text, parent)
        self.setFixedHeight(40)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumWidth(150)
        
        if icon_path:
            icon = QIcon(icon_path)
            self.setIcon(icon)
            self.setIconSize(QSize(20, 20))

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.hide()
        self.setWindowModality(Qt.ApplicationModal)
        self.setFixedSize(300, 250)
        
        self.scroll_area = None
        self.main_title = None
        self.theme_title = None
        self.theme_button = None
        self.back_button = None
        self.exit_button = None
        self.theme_buttons = {}
        self.current_theme = self.parent().current_theme
        
        # Create UI
        self.stacked_layout = QStackedLayout()
        self.main_settings_widget = self.create_main_settings()
        self.theme_settings_widget = self.create_theme_settings()
        
        self.stacked_layout.addWidget(self.main_settings_widget)
        self.stacked_layout.addWidget(self.theme_settings_widget)
        
        self.setLayout(self.stacked_layout)
        
        self.setWindowTitle("Settings")
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.WindowCloseButtonHint | Qt.MSWindowsFixedSizeDialogHint)
        
        self.apply_theme()
        self.update_theme_buttons()

    def create_main_settings(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        self.main_title = QLabel("Settings")
        self.main_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.main_title)
        
        layout.addSpacing(20)
        
        self.theme_button = QPushButton("Themes")
        self.theme_button.setFixedSize(150, 40)
        self.theme_button.clicked.connect(self.show_theme_settings)
        layout.addWidget(self.theme_button, alignment=Qt.AlignCenter)
        
        layout.addSpacing(20)
        
        self.exit_button = QPushButton("Exit Program")
        self.exit_button.setFixedSize(150, 40)
        self.exit_button.clicked.connect(self.parent().close)
        layout.addWidget(self.exit_button, alignment=Qt.AlignCenter)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_theme_settings(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        header_layout = QHBoxLayout()
        
        self.back_button = QPushButton()
        self.back_button.setIcon(QIcon('assets/icons/back_icon.png'))
        self.back_button.setIconSize(QSize(20, 20))
        self.back_button.setFixedSize(30, 30)
        self.back_button.clicked.connect(self.show_main_settings)
        header_layout.addWidget(self.back_button)
        
        self.theme_title = QLabel("Themes")
        self.theme_title.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(self.theme_title)
        
        spacer = QWidget()
        spacer.setFixedSize(30, 30)
        header_layout.addWidget(spacer)
        
        layout.addLayout(header_layout)
        layout.addSpacing(10)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        themes_container = QWidget()
        themes_layout = QVBoxLayout(themes_container)
        themes_layout.setSpacing(10)
        themes_layout.setContentsMargins(5, 5, 5, 5)
        
        self.theme_buttons = {}
        available_themes = ThemeManager.get_available_themes()
        
        for theme_id, theme_data in available_themes.items():
            button = ThemeButton(theme_data["name"], theme_data)
            button.clicked.connect(lambda checked, t=theme_id: self.change_theme(t))
            themes_layout.addWidget(button, alignment=Qt.AlignCenter)
            self.theme_buttons[theme_id] = button
        
        themes_layout.addStretch()
        self.scroll_area.setWidget(themes_container)
        layout.addWidget(self.scroll_area)
        
        widget.setLayout(layout)
        return widget

    def show_theme_settings(self):
        self.animation = QPropertyAnimation(self.theme_settings_widget, b"pos")
        self.animation.setDuration(300)
        self.animation.setStartValue(self.theme_settings_widget.pos() + QPoint(400, 0))
        self.animation.setEndValue(self.theme_settings_widget.pos())
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        
        self.stacked_layout.setCurrentWidget(self.theme_settings_widget)
        self.animation.start()
    
    def show_main_settings(self):
        self.animation = QPropertyAnimation(self.main_settings_widget, b"pos")
        self.animation.setDuration(300)
        self.animation.setStartValue(self.main_settings_widget.pos() - QPoint(400, 0))
        self.animation.setEndValue(self.main_settings_widget.pos())
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        
        self.stacked_layout.setCurrentWidget(self.main_settings_widget)
        self.animation.start()
    
    def change_theme(self, theme_id):
        try:
            theme_data = ThemeManager.get_available_themes()[theme_id]
            self.current_theme = theme_data["colors"]
            self.apply_theme()
            self.parent().apply_theme_colors(theme_data["colors"])
        except Exception as e:
            self.parent().show_error(f"Error changing theme: {str(e)}")

    def update_theme_buttons(self):
        """Update the styling of theme buttons"""
        if not hasattr(self, 'current_theme') or not self.theme_buttons:
            return
            
        colors = self.current_theme
        for button in self.theme_buttons.values():
            button.update_theme_colors(colors)
    
    def apply_theme(self):
        if not hasattr(self, 'current_theme'):
            return
            
        colors = self.current_theme
        
        if self.scroll_area:
            scroll_style = f"""
                QScrollArea {{
                    background-color: transparent;
                    border: none;
                }}
                QWidget#qt_scrollarea_viewport {{
                    background-color: transparent;
                }}
                QScrollBar:vertical {{
                    background-color: {colors['card_bg']};
                    width: 12px;
                    margin: 0;
                    border: none;
                }}
                QScrollBar::handle:vertical {{
                    background-color: {colors['button_bg']};
                    border-radius: 6px;
                    min-height: 20px;
                    margin: 2px;
                }}
                QScrollBar::add-line:vertical {{
                    height: 0px;
                    border: none;
                    background: none;
                }}
                QScrollBar::sub-line:vertical {{
                    height: 0px;
                    border: none;
                    background: none;
                }}
                QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                    background: none;
                    border: none;
                }}
            """
            
            self.scroll_area.setStyleSheet(scroll_style)
            viewport = self.scroll_area.viewport()
            viewport.setStyleSheet("background-color: transparent;")
            
            container = self.scroll_area.widget()
            if container:
                container.setStyleSheet("background-color: transparent;")
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {colors['card_bg']};
            }}
        """)
        
        title_style = f"""
            color: {colors['text']};
            font-size: 24px;
            font-weight: bold;
        """
        if self.main_title:
            self.main_title.setStyleSheet(title_style)
        if self.theme_title:
            self.theme_title.setStyleSheet(title_style)
        
        main_button_style = f"""
            QPushButton {{
                background-color: {colors['button_bg']};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {colors['button_hover']};
            }}
        """
        
        if self.theme_button:
            self.theme_button.setStyleSheet(main_button_style)
        
        if self.back_button:
            self.back_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {colors['button_bg']};
                    border: none;
                    border-radius: 15px;
                    padding: 5px;
                }}
                QPushButton:hover {{
                    background-color: {colors['button_hover']};
                }}
            """)
        
        if self.exit_button:
            self.exit_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {colors['error']};
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 10px;
                    font-size: 14px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: #c0392b;
                }}
            """)
        
        self.update_theme_buttons()  

class DuplicateFinderThread(QThread):
    update_progress = pyqtSignal(int)
    update_output = pyqtSignal(str)
    finished = pyqtSignal()
    
    def __init__(self, folder_path: str, action: str = 'move'):
        super().__init__()
        self.folder_path = folder_path
        self.action = action
        self.chunk_size = 8192
    
    def has_files_to_process(self) -> bool:
        try:
            files = [f for f in os.listdir(self.folder_path) 
                    if os.path.isfile(os.path.join(self.folder_path, f))]
            
            if not files:
                self.update_output.emit("No files found in the selected folder.")
                return False
                
            self.update_output.emit(f"Found {len(files)} files to check for duplicates.")
            return True
            
        except Exception as e:
            self.update_output.emit(f"Error accessing directory: {str(e)}")
            return False
        
    def get_file_hash(self, file_path: str) -> str:
        sha256_hash = hashlib.sha256()
        
        try:
            with open(file_path, "rb") as f:
                file_size = os.path.getsize(file_path)
                sha256_hash.update(str(file_size).encode())
                
                for byte_block in iter(lambda: f.read(self.chunk_size), b""):
                    sha256_hash.update(byte_block)
                    
            return sha256_hash.hexdigest()
        except Exception as e:
            self.update_output.emit(f"Error hashing file {file_path}: {str(e)}")
            return None
            
    def find_duplicates(self) -> Dict[str, List[str]]:
        hash_dict: Dict[str, List[str]] = {}
        
        try:
            files = [f for f in os.listdir(self.folder_path) 
                    if os.path.isfile(os.path.join(self.folder_path, f))]
            total_files = len(files)
            processed_files = 0
            
            size_dict: Dict[int, List[str]] = {}
            
            for filename in files:
                file_path = os.path.join(self.folder_path, filename)
                try:
                    file_size = os.path.getsize(file_path)
                    if file_size in size_dict:
                        size_dict[file_size].append(file_path)
                    else:
                        size_dict[file_size] = [file_path]
                        
                    processed_files += 1
                    progress = int((processed_files / (total_files * 2)) * 100)
                    self.update_progress.emit(progress)
                    
                except Exception as e:
                    self.update_output.emit(f"Error processing {filename}: {str(e)}")
            
            processed_files = 0
            for file_list in size_dict.values():
                if len(file_list) > 1:
                    for file_path in file_list:
                        file_hash = self.get_file_hash(file_path)
                        if file_hash:
                            if file_hash in hash_dict:
                                hash_dict[file_hash].append(file_path)
                            else:
                                hash_dict[file_hash] = [file_path]
                                
                        processed_files += 1
                        progress = 50 + int((processed_files / total_files) * 50)
                        self.update_progress.emit(progress)
            
            return {k: v for k, v in hash_dict.items() if len(v) > 1}
            
        except Exception as e:
            self.update_output.emit(f"Error accessing directory: {str(e)}")
            return {}
    
    def handle_duplicates(self, duplicates: Dict[str, List[str]]) -> Tuple[int, int]:
        total_duplicates = sum(len(files) - 1 for files in duplicates.values())
        handled_count = 0
        
        if self.action == 'move':
            duplicate_dir = os.path.join(self.folder_path, "Duplicates")
            os.makedirs(duplicate_dir, exist_ok=True)
        
        for hash_value, file_list in duplicates.items():
            # Keep the first file, handle all others
            original = file_list[0]
            for duplicate in file_list[1:]:
                try:
                    if self.action == 'move':
                        original_name = os.path.basename(duplicate)
                        new_path = os.path.join(duplicate_dir, original_name)
                        
                        # If a file with this name already exists, add a number
                        counter = 1
                        while os.path.exists(new_path):
                            base_name, ext = os.path.splitext(original_name)
                            new_path = os.path.join(duplicate_dir, f"{base_name} ({counter}){ext}")
                            counter += 1
                            
                        shutil.move(duplicate, new_path)
                        self.update_output.emit(f"Moved duplicate: {duplicate} → {new_path}")
                    else:
                        os.remove(duplicate)
                        self.update_output.emit(f"Deleted duplicate: {duplicate}")
                    handled_count += 1
                except Exception as e:
                    self.update_output.emit(f"Error handling duplicate {duplicate}: {str(e)}")
                    
        return total_duplicates, handled_count
    
    def run(self):
        try:
            # Check if there are any files to process
            if not self.has_files_to_process():
                self.finished.emit()
                return
            
            self.update_output.emit("Scanning for duplicate files in base folder...")
            duplicates = self.find_duplicates()
            
            if not duplicates:
                self.update_output.emit("No duplicate files found.")
                self.finished.emit()
                return
                
            total_dupes, handled_dupes = self.handle_duplicates(duplicates)
            
            self.update_output.emit(f"\nDuplicate handling complete:")
            self.update_output.emit(f"Total duplicate files found: {total_dupes}")
            self.update_output.emit(f"Duplicates {self.action}d: {handled_dupes}")
            
            if self.action == 'move':
                self.update_output.emit("\nDuplicate files have been moved to the 'Duplicates' folder.")
                self.update_output.emit("Please review before deleting.")
            
        except Exception as e:
            self.update_output.emit(f"Error during duplicate handling: {str(e)}")
        finally:
            self.finished.emit()

class DuplicateHandlerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_theme = self.parent().current_theme
        self.result = None
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Handle Duplicates")
        self.setWindowIcon(QIcon('assets/icons/app_icon.png'))
        
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        self.setFixedSize(400, 200)
        
        layout = QVBoxLayout()
        
        # Title and message
        title = QLabel("Choose Action")
        title.setAlignment(Qt.AlignCenter)
        message = QLabel("How would you like to handle duplicate files?")
        message.setAlignment(Qt.AlignCenter)
        message.setWordWrap(True)
        
        # Buttons
        button_layout = QHBoxLayout()
        move_button = QPushButton("Move to Folder")
        delete_button = QPushButton("Delete")
        cancel_button = QPushButton("Cancel")
        
        move_button.setFixedSize(120, 40)
        delete_button.setFixedSize(120, 40)
        cancel_button.setFixedSize(120, 40)
        
        move_button.clicked.connect(lambda: self.handle_choice('move'))
        delete_button.clicked.connect(lambda: self.handle_choice('delete'))
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(move_button)
        button_layout.addWidget(delete_button)
        button_layout.addWidget(cancel_button)
        
        layout.addSpacing(20)
        layout.addWidget(title)
        layout.addSpacing(10)
        layout.addWidget(message)
        layout.addSpacing(20)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Apply theme
        self.apply_theme_colors(self.current_theme)
    
    def handle_choice(self, action):
        self.result = action
        self.accept()
    
    def apply_theme_colors(self, colors):
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {colors['card_bg']};
            }}
            QLabel {{
                color: {colors['text']};
                font-size: 14px;
            }}
            QPushButton {{
                background-color: {colors['button_bg']};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {colors['button_hover']};
            }}
        """)
        
        for button in self.findChildren(QPushButton):
            if button.text() == "Delete":
                button.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {colors['error']};
                        color: white;
                        border: none;
                        border-radius: 5px;
                        padding: 10px;
                        font-size: 14px;
                        font-weight: bold;
                    }}
                    QPushButton:hover {{
                        background-color: #c0392b;
                    }}
                """)

class MetadataRemoverDialog(QDialog):
    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.current_theme = self.parent().current_theme
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        self.backup_path = None
        self.setup_ui()
        self.load_file_and_metadata()
        
    def setup_ui(self):
        self.setWindowTitle("Remove Metadata")
        self.setWindowIcon(QIcon('assets/icons/app_icon.png'))
        self.resize(800, 600)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Left side - File preview
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.setContentsMargins(20, 20, 20, 20)
        preview_widget.setFixedWidth(400)
        
        self.preview_label = QLabel("File Preview")
        self.preview_label.setAlignment(Qt.AlignCenter)
        preview_layout.addWidget(self.preview_label)
        
        image_container = QWidget()
        image_container_layout = QVBoxLayout(image_container)
        image_container_layout.setAlignment(Qt.AlignCenter)
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        image_container_layout.addWidget(self.image_label)
        
        preview_layout.addStretch(1)
        preview_layout.addWidget(image_container)
        preview_layout.addStretch(1)
        
        self.remove_button = QPushButton("Remove Metadata")
        self.remove_button.clicked.connect(self.remove_metadata)
        preview_layout.addWidget(self.remove_button)
        
        layout.addWidget(preview_widget)
        
        # Right side - Metadata
        metadata_widget = QWidget()
        metadata_layout = QVBoxLayout(metadata_widget)
        metadata_layout.setContentsMargins(20, 20, 20, 20)
        
        metadata_label = QLabel("Current Metadata")
        metadata_label.setAlignment(Qt.AlignCenter)
        metadata_layout.addWidget(metadata_label)
        
        self.metadata_text = QTextEdit()
        self.metadata_text.setReadOnly(True)
        metadata_layout.addWidget(self.metadata_text)
        
        layout.addWidget(metadata_widget)
        
        self.apply_theme()
    
    def remove_metadata(self):
        try:
            file_extension = os.path.splitext(self.file_path)[1].lower()
            
            # Create backup
            self.backup_path = self.file_path + '.backup'
            shutil.copy2(self.file_path, self.backup_path)
            
            if file_extension in IMAGE_FORMATS:
                try:
                    with Image.open(self.file_path) as img:
                        if img.mode in ('RGBA', 'LA'):
                            background = Image.new('RGB', img.size, (255, 255, 255))
                            if img.mode == 'RGBA':
                                background.paste(img, mask=img.split()[-1])
                            else:
                                background.paste(img, mask=img.split()[1])
                            img = background
                        
                        # Save without EXIF
                        data = list(img.getdata())
                        img_without_exif = Image.new(img.mode, img.size)
                        img_without_exif.putdata(data)
                        
                        # Save with original format if possible, otherwise JPEG
                        try:
                            img_without_exif.save(self.file_path, img.format if img.format else 'JPEG')
                        except:
                            img_without_exif.save(self.file_path, 'JPEG', quality=95)
                        
                except Exception as e:
                    raise Exception(f"Error removing image metadata: {str(e)}")
                
            elif file_extension in VIDEO_FORMATS:
                # Handle video files using exiftool
                try:
                    with exiftool.ExifToolHelper() as et:
                        et.execute('-overwrite_original', '-all=', '-tagsfromfile', '@', 'ColorSpaceTags', self.file_path)
                except Exception as e:
                    raise Exception(f"Error removing video metadata: {str(e)}")
            
            # Update preview and show success message
            self.load_file_and_metadata()
            QMessageBox.information(self, "Success", "Metadata successfully removed!")
            
            # Remove backup if successful
            if os.path.exists(self.backup_path):
                os.remove(self.backup_path)
            
        except Exception as e:
            # Restore from backup if it exists
            if self.backup_path and os.path.exists(self.backup_path):
                shutil.copy2(self.backup_path, self.file_path)
                os.remove(self.backup_path)
            
            QMessageBox.critical(self, "Error", f"Failed to remove metadata: {str(e)}")
            
    def update_preview(self):
        """Update the metadata preview after removal"""
        self.load_file_and_metadata()
    
    def load_file_and_metadata(self):
        file_extension = os.path.splitext(self.file_path)[1].lower()
        
        if file_extension in IMAGE_FORMATS:
            try:
                pixmap = QPixmap(self.file_path)
                scaled_pixmap = pixmap.scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.image_label.setPixmap(scaled_pixmap)
                
                with Image.open(self.file_path) as img:
                    metadata = self.extract_image_metadata(img)
                    formatted_metadata = self.format_metadata(metadata)
                    self.metadata_text.setText(formatted_metadata)
                    
            except Exception as e:
                self.metadata_text.setText(f"Error processing image: {str(e)}")
                self.image_label.setText("Error loading image preview")
                
        elif file_extension in VIDEO_FORMATS:
            self.image_label.setText("Video File\n(Preview not available)")
            self.image_label.setStyleSheet(f"color: {self.current_theme['text']};")
            
            # Extract metadata using exiftool for videos
            try:
                with exiftool.ExifToolHelper() as et:
                    metadata = et.get_metadata(self.file_path)[0]
                    
                    # Organize video metadata
                    organized_metadata = {
                        "File Info": {},
                        "Video Info": {},
                        "Audio Info": {},
                        "GPS Data": {},
                    }
                    
                    # Check if there's any metadata
                    if metadata:
                        for key, value in metadata.items():
                            if "GPS" in key or "Location" in key:
                                organized_metadata["GPS Data"][key] = value
                            elif "Audio" in key:
                                organized_metadata["Audio Info"][key] = value
                            elif "Video" in key or "Image" in key:
                                organized_metadata["Video Info"][key] = value
                            else:
                                organized_metadata["File Info"][key] = value
                    else:
                        for key in organized_metadata:
                            organized_metadata[key] = {"Status": "No data found"}
                    
                    formatted_metadata = self.format_metadata(organized_metadata)
                    self.metadata_text.setText(formatted_metadata)
                    
            except Exception as e:
                self.metadata_text.setText(f"Error reading video metadata: {str(e)}")
        else:
            self.image_label.setText("File Preview Not Available")
            self.image_label.setStyleSheet(f"color: {self.current_theme['text']};")
            self.metadata_text.setText("Unsupported file format")

    def extract_image_metadata(self, img):
        """Extract metadata from PIL Image object"""
        metadata = {"Basic Info": {}, "EXIF": {}, "GPS": {}}
        
        # Basic image info
        metadata["Basic Info"] = {
            "Format": img.format,
            "Mode": img.mode,
            "Size": f"{img.width} x {img.height}",
        }
        
        try:
            exif_data = img.info.get("exif")
            if exif_data:
                exif_dict = piexif.load(exif_data)
                
                # Extract EXIF data
                if "0th" in exif_dict and exif_dict["0th"]:
                    for tag_id, value in exif_dict["0th"].items():
                        tag_name = piexif.TAGS["0th"].get(tag_id, {}).get("name", str(tag_id))
                        if isinstance(value, bytes):
                            try:
                                value = value.decode()
                            except:
                                value = str(value)
                        metadata["EXIF"][tag_name] = value
                        
                # Extract GPS data
                if "GPS" in exif_dict and exif_dict["GPS"]:
                    gps_data = exif_dict["GPS"]
                    for tag_id, value in gps_data.items():
                        tag_name = piexif.TAGS["GPS"].get(tag_id, {}).get("name", str(tag_id))
                        metadata["GPS"][tag_name] = value
            else:
                metadata["EXIF"] = {"Status": "No EXIF data found"}
                metadata["GPS"] = {"Status": "No GPS data found"}
                
        except Exception as e:
            metadata["EXIF"] = {"Status": "No EXIF data found"}
            metadata["GPS"] = {"Status": "No GPS data found"}
                
        return metadata
    
    def format_metadata(self, metadata_dict):
        """Format metadata dictionary into readable text"""
        formatted_text = ""
        for category, data in metadata_dict.items():
            formatted_text += f"\n=== {category} ===\n"
            if isinstance(data, dict):
                if not data:
                    formatted_text += "No data available\n"
                else:
                    for key, value in data.items():
                        formatted_text += f"{key}: {value}\n"
            else:
                formatted_text += f"{data}\n"
        return formatted_text
    
    def apply_theme(self):
        colors = self.current_theme
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {colors['card_bg']};
            }}
            QLabel {{
                color: {colors['text']};
                font-size: 14px;
                padding: 5px;
            }}
            QTextEdit {{
                background-color: {colors['input_bg']};
                color: {colors['text']};
                border: none;
                border-radius: 5px;
                padding: 10px;
            }}
            QPushButton {{
                background-color: {colors['error']};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
                height: 40px;
            }}
            QPushButton:hover {{
                background-color: #c0392b;
            }}
            QScrollBar:vertical {{
                background-color: {colors['card_bg']};
                width: 12px;
                margin: 0px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background-color: {colors['button_bg']};
                border-radius: 6px;
                min-height: 20px;
                margin: 2px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
                border: none;
                background: none;
            }}
        """)

class MapChoiceDialog(QDialog):
    def __init__(self, us_locations, world_countries, parent=None):
        super().__init__(parent)
        self.current_theme = self.parent().current_theme
        self.selected_map = None
        self.us_locations = us_locations
        self.world_countries = world_countries
        self.us_svg = None
        self.world_svg = None
        self.map_dialog = None
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Choose Map Type")
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        locations_text = ""
        if self.us_locations:
            locations_text += f"US States Found: {', '.join(self.us_locations)}\n\n"
        if self.world_countries:
            locations_text += f"Other Countries Found: {', '.join(self.world_countries)}"
            
        info_label = QLabel(locations_text)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        us_button = QPushButton("Show US Map")
        world_button = QPushButton("Show World Map")
        
        us_button.setEnabled(bool(self.us_locations))
        world_button.setEnabled(bool(self.world_countries))
        
        us_button.clicked.connect(lambda: self.show_map('us'))
        world_button.clicked.connect(lambda: self.show_map('world'))
        
        layout.addWidget(us_button)
        layout.addWidget(world_button)
        
        self.setLayout(layout)
        self.apply_theme()

    def store_svg_content(self, us_svg, world_svg):
        """Store SVG content for reuse"""
        self.us_svg = us_svg
        self.world_svg = world_svg
        
    def show_map(self, map_type):
        """Show the selected map"""
        try:
            self.selected_map = map_type
            svg_content = self.us_svg if map_type == 'us' else self.world_svg
            
            if svg_content:
                # Create new map dialog
                self.map_dialog = StateMapDialog(svg_content, self, self.us_svg, self.world_svg)
                self.map_dialog.exec_()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error showing map: {str(e)}")
            
    def closeEvent(self, event):
        """Handle closing of the dialog"""
        if self.map_dialog:
            self.map_dialog.close()
            self.map_dialog.deleteLater()
            self.map_dialog = None
        super().closeEvent(event)
            
    def apply_theme(self):
        colors = self.current_theme
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {colors['card_bg']};
            }}
            QLabel {{
                color: {colors['text']};
                font-size: 14px;
                padding: 10px;
            }}
            QPushButton {{
                background-color: {colors['button_bg']};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
                height: 40px;
                margin: 5px;
            }}
            QPushButton:hover {{
                background-color: {colors['button_hover']};
            }}
            QPushButton:disabled {{
                background-color: {colors['input_bg']};
                color: {colors['secondary_text']};
            }}
        """)

class StateMapDialog(QDialog):
    def __init__(self, svg_content, parent=None, us_svg=None, world_svg=None):
        super().__init__(parent)
        self.current_theme = self.parent().current_theme
        self.svg_content = svg_content
        self.us_svg = us_svg
        self.world_svg = world_svg
        self.current_map = 'us' if svg_content == us_svg else 'world'
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        self.is_saving = False
        self.temp_file = None
        self.web_view = None
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Media Location Map")
        self.setMinimumSize(1000, 600)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Top container for buttons
        top_container = QWidget()
        top_container.setFixedHeight(60)
        top_container.setStyleSheet(f"background-color: {self.current_theme['card_bg']};")
        top_layout = QHBoxLayout(top_container)
        top_layout.setContentsMargins(10, 10, 10, 10)
        
        # Left dummy widget to match save button width
        dummy_left = QWidget()
        dummy_left.setFixedWidth(40)
        top_layout.addWidget(dummy_left)
        
        # Switch map button
        switch_map_button = QPushButton("Switch to " + ("World Map" if self.current_map == 'us' else "US Map"))
        switch_map_button.setFixedSize(300, 40)
        switch_map_button.clicked.connect(self.switch_map)
        switch_map_button.setCursor(Qt.PointingHandCursor)
        top_layout.addWidget(switch_map_button, 1, Qt.AlignCenter)
        
        # Save button
        save_button = QPushButton()
        save_button.setIcon(QIcon('assets/icons/save_icon.png'))
        save_button.setIconSize(QSize(20, 20))
        save_button.setFixedSize(40, 40)
        save_button.clicked.connect(lambda: self.show_save_menu(save_button))
        save_button.setCursor(Qt.PointingHandCursor)
        top_layout.addWidget(save_button)
        
        main_layout.addWidget(top_container)
        
        # Container for the web view
        self.web_container = QWidget()
        web_layout = QVBoxLayout(self.web_container)
        web_layout.setContentsMargins(0, 0, 0, 0)
        
        self.web_view = QWebEngineView()
        web_layout.addWidget(self.web_view)
        
        main_layout.addWidget(self.web_container)
        
        self.load_current_map()
        self.apply_theme()
        
    def switch_map(self):
        try:
            self.current_map = 'world' if self.current_map == 'us' else 'us'
            self.svg_content = self.us_svg if self.current_map == 'us' else self.world_svg
            
            for button in self.findChildren(QPushButton):
                if button.text().startswith("Switch"):
                    button.setText("Switch to " + ("World Map" if self.current_map == 'us' else "US Map"))
            
            self.load_current_map()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error switching maps: {str(e)}")

    def load_current_map(self):
        try:
            if self.temp_file and os.path.exists(self.temp_file):
                try:
                    os.unlink(self.temp_file)
                except:
                    pass
            
            # Create the HTML content
            with tempfile.NamedTemporaryFile('w', delete=False, suffix='.html') as f:
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <style>
                        body {{ 
                            margin: 0;
                            padding: 0;
                            background-color: {self.current_theme['card_bg']};
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            height: 100vh;
                            overflow: hidden;
                        }}
                        svg {{
                            max-width: 95%;
                            max-height: 95vh;
                            height: auto;
                        }}
                    </style>
                </head>
                <body>
                    {self.svg_content}
                </body>
                </html>
                """
                f.write(html_content)
                self.temp_file = f.name
            
            self.web_view.setUrl(QUrl.fromLocalFile(self.temp_file))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading map: {str(e)}")

    def show_save_menu(self, button):
        if self.is_saving:
            return
            
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {self.current_theme['card_bg']};
                color: {self.current_theme['text']};
                border: 1px solid {self.current_theme['button_bg']};
            }}
            QMenu::item:selected {{
                background-color: {self.current_theme['button_bg']};
            }}
        """)
        
        save_svg_action = menu.addAction("Save as SVG")
        save_png_action = menu.addAction("Save as PNG")
        
        pos = button.mapToGlobal(button.rect().bottomLeft())
        action = menu.exec_(pos)
        
        if action == save_svg_action:
            self.save_map('svg')
        elif action == save_png_action:
            self.save_map('png')

    def save_map(self, format_type='svg'):
        if self.is_saving:
            return
            
        self.is_saving = True
        try:
            if format_type == 'svg':
                file_filter = "SVG files (*.svg)"
                default_path = os.path.expanduser("~/Downloads/map.svg")
            else:
                file_filter = "PNG files (*.png)"
                default_path = os.path.expanduser("~/Downloads/map.png")

            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Map",
                default_path,
                file_filter
            )
            
            if file_path:
                try:
                    if format_type == 'svg':
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(self.svg_content)
                    else:  # PNG
                        self.web_view.page().toHtml(lambda _: None)
                        size = self.web_container.size()
                        image = QImage(size, QImage.Format_ARGB32)
                        image.fill(QColor(self.current_theme['card_bg']))
                        painter = QPainter(image)
                        self.web_container.render(painter)
                        painter.end()
                        image.save(file_path, 'PNG')
                    
                    QMessageBox.information(self, "Success", f"Map saved successfully to:\n{file_path}")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Error saving map: {str(e)}")
        finally:
            self.is_saving = False

    def closeEvent(self, event):
        """Handle dialog close"""
        if self.web_view:
            self.web_view.stop()
            self.web_view.page().deleteLater()
        if self.temp_file and os.path.exists(self.temp_file):
            try:
                os.unlink(self.temp_file)
            except:
                pass
        super().closeEvent(event)

    def apply_theme(self):
        colors = self.current_theme
        
        # Style for the switch map button
        switch_button_style = f"""
            QPushButton {{
                background-color: {colors['button_bg']};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px 20px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {colors['button_hover']};
            }}
        """
        
        # Style for the save button
        save_button_style = f"""
            QPushButton {{
                background-color: {colors['button_bg']};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px;
            }}
            QPushButton:hover {{
                background-color: {colors['button_hover']};
            }}
        """
        
        # Apply specific styles to buttons
        for button in self.findChildren(QPushButton):
            if button.text().startswith("Switch"):
                button.setStyleSheet(switch_button_style)
            else:
                button.setStyleSheet(save_button_style)

class MediaGPSExtractorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(600, 400)
        self.is_fullscreen = True
        default_theme = ThemeManager.get_default_theme()
        self.current_theme = default_theme["colors"]
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.showFullScreen()
        self.windowed_size = QSize(800, 600)
        self.current_worker = None
        self.files_processed = False
        
        self.settings_dialog = SettingsDialog(self)
        
        self.initUI()
        self.apply_theme_colors(self.current_theme)

    def initUI(self):
        self.setWindowTitle('PicPoint')
        self.setWindowIcon(QIcon('assets/icons/app_icon.png'))

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)

        content_card = CardWidget()
        card_layout = QVBoxLayout(content_card)

        # Header section
        header_container = QWidget()
        header_layout = QVBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 20)

        top_bar = QWidget()
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(0, 0, 0, 0)

        dummy_left = QWidget()
        dummy_left.setFixedWidth(40)
        top_bar_layout.addWidget(dummy_left)

        self.header = QLabel("PicPoint")
        self.header.setAlignment(Qt.AlignCenter)
        top_bar_layout.addWidget(self.header, 1)

        settings_button = QPushButton()
        settings_button.setIcon(QIcon('assets/icons/setting_icon.png'))
        settings_button.setIconSize(QSize(20, 20))
        settings_button.setFixedSize(40, 40)
        settings_button.clicked.connect(self.show_settings)
        top_bar_layout.addWidget(settings_button)

        header_layout.addWidget(top_bar)
        card_layout.addWidget(header_container)

        # Folder selection section
        folder_layout = QHBoxLayout()
        folder_layout.setSpacing(10)

        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText("Select a folder")
        self.folder_input.setFixedHeight(40)
        folder_layout.addWidget(self.folder_input)
        
        browse_button = QPushButton('Browse')
        browse_button.setFixedSize(100, 40)
        browse_button.clicked.connect(self.browse_folder)
        browse_button.setCursor(Qt.PointingHandCursor)
        folder_layout.addWidget(browse_button)
        
        card_layout.addLayout(folder_layout)

        # Action buttons section - First row
        button_layout_1 = QHBoxLayout()
        button_layout_1.setSpacing(10)

        location_button = ModernButton('Location Sort', 'assets/icons/location_icon.png')
        location_button.clicked.connect(self.sort_by_loc)
        button_layout_1.addWidget(location_button)

        time_button = ModernButton('Time Sort', 'assets/icons/date_icon.png')
        time_button.clicked.connect(self.sort_by_time)
        button_layout_1.addWidget(time_button)

        flatten_button = ModernButton('Flatten Folder', 'assets/icons/flatten_icon.png')
        flatten_button.clicked.connect(self.flatten_folder)
        button_layout_1.addWidget(flatten_button)

        card_layout.addLayout(button_layout_1)

        # Action buttons section - Second row
        button_layout_2 = QHBoxLayout()
        button_layout_2.setSpacing(10)

        generate_map_button = ModernButton('Generate Map', 'assets/icons/map_icon.png')
        generate_map_button.clicked.connect(self.generate_map)
        button_layout_2.addWidget(generate_map_button)

        remove_duplicates_button = ModernButton('Remove Duplicates', 'assets/icons/duplicate_icon.png')
        remove_duplicates_button.clicked.connect(self.handle_duplicates)
        button_layout_2.addWidget(remove_duplicates_button)

        remove_metadata_button = ModernButton('Remove Metadata', 'assets/icons/remove_icon.png')
        remove_metadata_button.clicked.connect(self.remove_metadata)
        button_layout_2.addWidget(remove_metadata_button)

        card_layout.addLayout(button_layout_2)

        # Progress and status section
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(10)
        card_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(self.status_label)

        # Output area
        output_scroll = QScrollArea()
        output_scroll.setWidgetResizable(True)
        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        self.output_area.setFont(QFont('Inter', 12))
        self.output_area.textChanged.connect(self.check_scrollbar)
        output_scroll.setWidget(self.output_area)
        card_layout.addWidget(output_scroll)

        main_layout.addWidget(content_card)

    def show_post_sort_dialog(self, sort_type):
        dialog = PostSortDialog(self, sort_type)
        dialog.exec_()
        return dialog.result

    def check_scrollbar(self):
        """Check if scrollbar is needed and apply theme if it is"""
        document_height = self.output_area.document().size().height()
        viewport_height = self.output_area.viewport().height()
        
        self.apply_scrollbar_theme()

    def apply_scrollbar_theme(self):
        """Apply theme colors specifically to scrollbar"""
        colors = self.current_theme
        scrollbar_style = f"""
            QTextEdit {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: {colors['border']};
                padding: 10px;
            }}
            QScrollBar:vertical {{
                background-color: {colors['card_bg']};
                width: 12px;
                margin: 0px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background-color: {colors['button_bg']};
                border-radius: 6px;
                min-height: 20px;
                margin: 2px;
            }}
            QScrollBar::add-line:vertical {{
                height: 0px;
                border: none;
                background: none;
            }}
            QScrollBar::sub-line:vertical {{
                height: 0px;
                border: none;
                background: none;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
                border: none;
            }}
        """
        
        self.output_area.setStyleSheet(scrollbar_style)
        
        scroll_style = f"""
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            QWidget#qt_scrollarea_viewport {{
                background-color: transparent;
            }}
            QScrollBar:vertical {{
                background-color: {colors['card_bg']};
                width: 12px;
                margin: 0px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background-color: {colors['button_bg']};
                border-radius: 6px;
                min-height: 20px;
                margin: 2px;
            }}
            QScrollBar::add-line:vertical {{
                height: 0px;
                border: none;
                background: none;
            }}
            QScrollBar::sub-line:vertical {{
                height: 0px;
                border: none;
                background: none;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
                border: none;
            }}
        """
        
        for scroll_area in self.findChildren(QScrollArea):
            scroll_area.setStyleSheet(scroll_style)
            viewport = scroll_area.viewport()
            viewport.setStyleSheet("background-color: transparent;")

    def show_settings(self):
        """Show the pre-initialized settings dialog"""
        self.settings_dialog.show()

    def toggle_fullscreen(self):
        if self.is_fullscreen:
            self.showNormal()
            self.setGeometry(100, 100, self.windowed_size.width(), self.windowed_size.height())
            self.center()
        else:
            self.showFullScreen()
        self.is_fullscreen = not self.is_fullscreen

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.toggle_fullscreen()

    def center(self):
        frame_geometry = self.frameGeometry()
        screen_center = QDesktopWidget().availableGeometry().center()
        frame_geometry.moveCenter(screen_center)
        self.move(frame_geometry.topLeft())

    def browse_folder(self):
        downloads_path = os.path.expanduser("~/Downloads")
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Directory",
            downloads_path
        )
        if folder:
            self.folder_input.setText(folder)

    def sort_by_loc(self, is_additional_sort=False):
        if not self.check_and_prepare_operation():
            return

        self.files_processed = False
        folder_path = self.folder_input.text()
        self.current_worker = SortByLocThread(folder_path, is_additional_sort)
        self.current_worker.update_progress.connect(self.update_progress)
        self.current_worker.update_output.connect(self.update_output)
        self.current_worker.finished.connect(lambda: self.sort_loc_finished(not is_additional_sort))
        self.current_worker.file_processed.connect(self.set_files_processed)
        self.current_worker.internet_check_failed.connect(self.handle_internet_check_failed)
        self.current_worker.start()

    def handle_internet_check_failed(self):
        """Handle the case when internet check fails"""
        self.cleanup_worker()
        self.status_label.setText("Ready")
        self.status_label.setStyleSheet(f"color: {self.current_theme['secondary_text']}; margin-top: 5px;")
        self.progress_bar.setValue(0)

    def flatten_finished(self):
        self.operation_finished("")

    def sort_by_time(self, is_additional_sort=False):
        if not self.check_and_prepare_operation():
            return

        self.files_processed = False
        folder_path = self.folder_input.text()
        self.current_worker = SortByTimeThread(folder_path, is_additional_sort)
        self.current_worker.update_progress.connect(self.update_progress)
        self.current_worker.update_output.connect(self.update_output)
        self.current_worker.finished.connect(lambda: self.sort_time_finished(not is_additional_sort))
        self.current_worker.file_processed.connect(self.set_files_processed)
        self.current_worker.start()

    def generate_map(self):
        if not self.check_and_prepare_operation():
            return

        us_svg_path = os.path.join(os.path.dirname(__file__), 'assets', 'us_map.svg')
        world_svg_path = os.path.join(os.path.dirname(__file__), 'assets', 'world_map.svg')
        
        if not os.path.exists(us_svg_path) or not os.path.exists(world_svg_path):
            self.show_error("Map SVG files not found")
            return

        self.current_worker = MapGenerationThread(self.folder_input.text(), us_svg_path, world_svg_path)
        self.current_worker.update_progress.connect(self.update_progress)
        self.current_worker.update_output.connect(self.update_output)
        self.current_worker.finished.connect(self.map_generation_finished)
        self.current_worker.internet_check_failed.connect(self.handle_internet_check_failed)
        self.current_worker.start()

    def map_generation_finished(self, us_states, world_countries, us_svg, world_svg):
        self.operation_finished("Map generation completed")
        
        if not us_states and not world_countries:
            self.update_output("No locations found in media files")
            return
            
        dialog = MapChoiceDialog(us_states, world_countries, self)
        dialog.store_svg_content(us_svg, world_svg)  # Store SVG content for reuse
        dialog.exec_()

    def handle_duplicates(self):
        """Handle the duplicate file detection and removal process."""
        if not self.check_and_prepare_operation():
            return
            
        # Check if there are any files to process first
        try:
            files = [f for f in os.listdir(self.folder_input.text()) 
                    if os.path.isfile(os.path.join(self.folder_input.text(), f))]
            
            if not files:
                self.output_area.clear()
                self.update_output("No files found in the selected folder.")
                return
                
            # Only show dialog if we found files to process
            dialog = DuplicateHandlerDialog(self)
            if dialog.exec_() == QDialog.Accepted and dialog.result:
                try:
                    self.status_label.setText("Processing")
                    self.status_label.setStyleSheet(f"color: {self.current_theme['warning']}; margin-top: 5px;")
                    self.progress_bar.setValue(0)
                    
                    self.current_worker = DuplicateFinderThread(self.folder_input.text(), dialog.result)
                    self.current_worker.update_progress.connect(self.update_progress)
                    self.current_worker.update_output.connect(self.update_output)

                    self.current_worker.finished.connect(lambda: self.operation_finished(""))
                    self.current_worker.start()
                    
                except Exception as e:
                    self.show_error(f"Error starting duplicate handler: {str(e)}")
                    self.status_label.setText("Ready")
                    self.status_label.setStyleSheet(f"color: {self.current_theme['secondary_text']}; margin-top: 5px;")
                    self.progress_bar.setValue(0)
            else:
                self.output_area.clear()
                self.status_label.setText("Ready")
                self.status_label.setStyleSheet(f"color: {self.current_theme['secondary_text']}; margin-top: 5px;")
                self.progress_bar.setValue(0)
                    
        except Exception as e:
            self.show_error(f"Error accessing directory: {str(e)}")
        
    def remove_metadata(self):
        """Open file dialog and remove metadata from selected file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File",
            self.folder_input.text() or os.path.expanduser("~/Downloads"),
            f"Media Files (*{' *'.join(SUPPORTED_MEDIA_FORMATS)});;All Files (*.*)"
        )
        
        if file_path:
            try:
                dialog = MetadataRemoverDialog(file_path, self)
                dialog.exec_()
            except Exception as e:
                self.show_error(f"Error removing metadata: {str(e)}")

    def set_files_processed(self):
        self.files_processed = True

    def check_and_prepare_operation(self):
        """Check if operation can proceed and prepare the UI"""
        folder_path = self.folder_input.text()
        if not folder_path:
            self.show_error("Please select a folder")
            return False

        if self.current_worker and self.current_worker.isRunning():
            self.show_error("An operation is already in progress")
            return False

        self.cleanup_worker()
        self.output_area.clear()
        self.progress_bar.setValue(0)
        self.status_label.setText("Processing")
        self.status_label.setStyleSheet(f"color: {self.current_theme['warning']}; margin-top: 5px;")
        return True

    def cleanup_worker(self):
        if self.current_worker:
            if self.current_worker.isRunning():
                self.current_worker.quit()
                self.current_worker.wait()
            self.current_worker.deleteLater()
            self.current_worker = None

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def update_output(self, message):
        self.output_area.append(message)
        self.check_scrollbar()

    def sort_loc_finished(self, show_dialog=True):
        self.operation_finished(None)
        
        if show_dialog and self.files_processed and self.show_post_sort_dialog("location"):
            self.status_label.setText("Starting date sort...")
            self.progress_bar.setValue(0)
            self.sort_by_time(is_additional_sort=True)

    def flatten_folder(self):
        """Handle the flatten folder operation"""
        if not self.check_and_prepare_operation():
            return

        self.current_worker = FlattenFolderThread(self.folder_input.text())
        self.current_worker.update_progress.connect(self.update_progress)
        self.current_worker.update_output.connect(self.update_output)
        self.current_worker.finished.connect(self.flatten_finished)
        self.current_worker.start()

    def flatten_finished(self):
        """Handle completion of flatten folder operation"""
        self.operation_finished("")

    def sort_time_finished(self, show_dialog=True):
        self.operation_finished(None)
        
        if show_dialog and self.files_processed and self.show_post_sort_dialog("time"):
            self.status_label.setText("Starting location sort...")
            self.progress_bar.setValue(0)
            self.sort_by_loc(is_additional_sort=True)

    def operation_finished(self, message):
        self.progress_bar.setValue(100)
        if message:
            self.output_area.append(message)
        self.status_label.setText("Completed")
        self.status_label.setStyleSheet(f"color: {self.current_theme['success']}; margin-top: 5px;")
        self.cleanup_worker()

    def closeEvent(self, event):
        self.cleanup_worker()
        super().closeEvent(event)

    def apply_theme_colors(self, colors):
        self.current_theme = colors
        
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {colors['main_bg']};
            }}
            QToolTip {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: none;
                padding: 5px;
            }}
        """)
        
        for card in self.findChildren(CardWidget):
            card.setStyleSheet(f"""
                QFrame#card {{
                    background-color: {colors['card_bg']};
                    border-radius: 10px;
                    padding: 20px;
                    margin: 20px;
                    border: {colors['border']};
                }}
            """)

        self.header.setStyleSheet(f"""
            font-size: 28px;
            color: {colors['text']};
            font-weight: bold;
        """)

        self.folder_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {colors['input_bg']};
                color: {colors['text']};
                border: {colors['border']};
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
            }}
        """)

        browse_button_style = f"""
            QPushButton {{
                background-color: {colors['button_bg']};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 0 15px;
                font-size: 14px;
                font-weight: bold;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: {colors['button_hover']};
            }}
        """
        
        for button in self.findChildren(QPushButton):
            if button.text() == 'Browse':
                button.setStyleSheet(browse_button_style)

        modern_button_style = f"""
            QPushButton {{
                background-color: {colors['button_bg']};
                color: white;
                border: none;
                border-radius: 5px;
                padding-left: 15px;
                padding-right: 40px;
                font-size: 14px;
                font-weight: bold;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: {colors['button_hover']};
            }}
            QPushButton:pressed {{
                background-color: {colors['button_pressed']};
            }}
            QPushButton::icon {{
                position: absolute;
                left: 15px;
            }}
        """
        
        for button in self.findChildren(ModernButton):
            button.setStyleSheet(modern_button_style)

        settings_button_style = f"""
            QPushButton {{
                background-color: {colors['button_bg']};
                border: none;
                border-radius: 5px;
            }}
            QPushButton:hover {{
                background-color: {colors['button_hover']};
            }}
        """
        
        for button in self.findChildren(QPushButton):
            if not button.text() and button.icon():
                button.setStyleSheet(settings_button_style)

        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {colors['progress_bg']};
                border: {colors['border']};
                border-radius: 5px;
            }}
            QProgressBar::chunk {{
                background-color: {colors['progress_chunk']};
                border-radius: 5px;
            }}
        """)

        self.status_label.setStyleSheet(f"color: {colors['secondary_text']}; margin-top: 5px;")

        self.apply_scrollbar_theme()

    def show_error(self, message):
        """Display error message in the output area"""
        self.output_area.append(f"<span style='color: {self.current_theme['error']};'>{message}</span>")