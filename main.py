import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont, QFontDatabase
from gui import MediaGPSExtractorGUI
from gui import SettingsDialog
from theme_manager import ThemeManager

def main():
    app = QApplication(sys.argv)
    
    # Load custom font
    font_id = QFontDatabase.addApplicationFont("assets/fonts/Inter-Regular.ttf")
    if font_id != -1:
        font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
        app.setFont(QFont(font_family, 10))
    else:
        print("Error: Failed to load custom font")
    
    # Create  main window
    ex = MediaGPSExtractorGUI()
    
    # Apply default theme
    default_theme = ThemeManager.get_default_theme()
    ex.apply_theme_colors(default_theme["colors"])
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()