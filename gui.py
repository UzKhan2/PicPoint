from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QFileDialog, QProgressBar, QTextEdit, QLabel, 
                             QLineEdit, QFrame, QScrollArea, QDesktopWidget, QDialog,
                             QStackedLayout)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QSize, QPoint
from PyQt5.QtGui import QFont, QIcon, QFontDatabase
from utils import check_internet_connection
from workers import SortByLocThread, FlattenFolderThread, SortByTimeThread
from theme_manager import ThemeManager
import os

class PostSortDialog(QDialog):
    def __init__(self, parent=None, sort_type="location"):
        super().__init__(parent)
        self.sort_type = sort_type
        self.result = None
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("PinPoint")
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
        self.setWindowTitle('PinPoint')
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

        self.header = QLabel("PinPoint")
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

        # Action buttons section
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        location_button = ModernButton('Location Sort', 'assets/icons/play_icon.png')
        location_button.clicked.connect(self.sort_by_loc)
        button_layout.addWidget(location_button)

        time_button = ModernButton('Time Sort', 'assets/icons/clock_icon.png')
        time_button.clicked.connect(self.sort_by_time)
        button_layout.addWidget(time_button)

        flatten_button = ModernButton('Flatten Folder', 'assets/icons/flatten_icon.png')
        flatten_button.clicked.connect(self.flatten_folder)
        button_layout.addWidget(flatten_button)

        card_layout.addLayout(button_layout)

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

    def flatten_folder(self):
        if not self.check_and_prepare_operation():
            return

        self.current_worker = FlattenFolderThread(self.folder_input.text())
        self.current_worker.update_progress.connect(self.update_progress)
        self.current_worker.update_output.connect(self.update_output)
        self.current_worker.finished.connect(self.flatten_finished)
        self.current_worker.start()

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
        self.output_area.append("Starting operation...")
        self.status_label.setText("Processing")
        self.status_label.setStyleSheet(f"color: {self.current_theme['warning']}; margin-top: 5px;")
        return True

    def cleanup_worker(self):
        """Safely clean up the current worker thread"""
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

    def flatten_finished(self):
        self.operation_finished("Folder flattening completed")

    def sort_time_finished(self, show_dialog=True):
        self.operation_finished(None)
        
        if show_dialog and self.files_processed and self.show_post_sort_dialog("time"):
            self.status_label.setText("Starting location sort...")
            self.progress_bar.setValue(0)
            self.sort_by_loc(is_additional_sort=True)

    def operation_finished(self, message):
        """Common handling for operation completion"""
        self.progress_bar.setValue(100)
        if message:
            self.output_area.append(message)
        self.status_label.setText("Completed")
        self.status_label.setStyleSheet(f"color: {self.current_theme['success']}; margin-top: 5px;")
        self.cleanup_worker()

    def closeEvent(self, event):
        """Clean up worker threads when closing the application"""
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