import sys
import os
import time
import shutil
import logging
import platform
import json

# Check OS for sound support
if platform.system() == "Windows":
    import winsound

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QSystemTrayIcon, QMenu, QFileDialog, QCheckBox,
                             QMessageBox, QFrame, QSpinBox, QComboBox,
                             QInputDialog, QListView, QDialog, QDialogButtonBox,
                             QRadioButton, QButtonGroup)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QAction, QFont

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# --- CONFIGURATION PATH ---
# This ensures the config.json is always created next to the script file
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.json")

# --- DARK MODE STYLESHEET ---
STYLESHEET = """
QMainWindow {
    background-color: #1C1C1E;
}
QWidget {
    color: #F5F5F7;
    font-family: 'Segoe UI', 'San Francisco', sans-serif;
    font-size: 13px;
}
QLabel#HeaderTitle {
    font-size: 22px;
    font-weight: 700;
    color: #FFFFFF;
}
QLabel#SectionLabel {
    font-weight: 600;
    font-size: 11px;
    color: #98989D;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-bottom: 4px;
}
QFrame#Card {
    background-color: #2C2C2E;
    border-radius: 12px;
    border: 1px solid #3A3A3C;
}
QLineEdit {
    background-color: #1C1C1E;
    border: 1px solid #3A3A3C;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
    color: #FFFFFF;
    selection-background-color: #0A84FF;
}
QLineEdit:focus {
    border: 1px solid #0A84FF;
    background-color: #000000;
}
QLineEdit:disabled {
    color: #636366;
    background-color: #252527;
    border: 1px solid #2C2C2E;
}
QPushButton {
    background-color: #3A3A3C;
    border: 1px solid #48484A;
    border-radius: 8px;
    padding: 6px 12px;
    font-weight: 500;
    color: #FFFFFF;
}
QPushButton:hover {
    background-color: #48484A;
}
QPushButton:pressed {
    background-color: #2C2C2E;
}
QPushButton#PrimaryBtn {
    background-color: #0A84FF;
    border: none;
    font-weight: 600;
}
QPushButton#PrimaryBtn:hover {
    background-color: #0077ED;
}
QPushButton#StartBtn {
    background-color: #30D158;
    color: #000000;
    font-size: 16px;
    font-weight: 800;
    border-radius: 12px;
    padding: 15px;
    border: none;
}
QPushButton#StartBtn:hover {
    background-color: #28CD41;
}
QPushButton#StopBtn {
    background-color: #FF453A;
    color: #FFFFFF;
    font-size: 16px;
    font-weight: 800;
    border-radius: 12px;
    padding: 15px;
    border: none;
}
QPushButton#StopBtn:hover {
    background-color: #FF3B30;
}
QComboBox, QSpinBox {
    border: 1px solid #3A3A3C;
    border-radius: 8px;
    padding: 5px 10px;
    background-color: #1C1C1E;
    color: #FFFFFF;
    selection-background-color: #0A84FF;
}
QComboBox::drop-down {
    border: none;
    width: 25px;
    subcontrol-origin: padding;
    subcontrol-position: center right;
    padding-right: 5px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #F5F5F7;
    width: 0;
    height: 0;
}
QComboBox QAbstractItemView {
    background-color: #2C2C2E;
    color: #FFFFFF;
    selection-background-color: #0A84FF;
    border: 1px solid #3A3A3C;
    outline: none;
}
QCheckBox {
    spacing: 8px;
    color: #F5F5F7;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 9px;
    border: 2px solid #636366;
    background: #1C1C1E;
}
QCheckBox::indicator:checked {
    background-color: #0A84FF;
    border: 2px solid #0A84FF;
    border-radius: 9px;
    image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSIzIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiPjxwb2x5bGluZSBwb2ludHM9IjIwIDYgOSAxNyA0IDEyIi8+PC9zdmc+);
}
QRadioButton {
    spacing: 8px;
    color: #F5F5F7;
}
QRadioButton::indicator {
    width: 18px;
    height: 18px;
    border-radius: 9px;
    border: 2px solid #636366;
    background: #1C1C1E;
}
QRadioButton::indicator:checked {
    border-radius: 9px;
    border: 2px solid #0A84FF;
    background-color: #0A84FF;
    background-image: radial-gradient(circle, #FFFFFF 0%, #FFFFFF 35%, transparent 35%, transparent 100%);
}
QLabel#StatusPill {
    background-color: #2C2C2E;
    color: #8E8E93;
    border-radius: 12px;
    padding: 4px 12px;
    font-size: 12px;
    font-weight: 700;
    border: 1px solid #3A3A3C;
}
QLabel#StatusPill[active="true"] {
    background-color: #102A1C;
    color: #30D158;
    border: 1px solid #1B4028;
}
"""

class FileMoverWorker(QThread):
    status_update = pyqtSignal(str)
    file_moved = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.running = False
        self.source_path = ""
        self.dest_path = ""
        self.filename = ""
        self.check_interval = 3
        self.mode = "move"

    def set_params(self, source, dest, filename, interval, mode):
        self.source_path = source
        self.dest_path = dest
        self.filename = filename
        self.check_interval = interval
        self.mode = mode

    def run(self):
        self.running = True
        self.status_update.emit(f"Watching: {self.filename}")
        
        while self.running:
            try:
                if not all([self.source_path, self.dest_path, self.filename]):
                    time.sleep(1)
                    continue

                src_file = os.path.join(self.source_path, self.filename)
                dst_file = os.path.join(self.dest_path, self.filename)

                if os.path.exists(src_file):
                    if self.is_file_stable(src_file):
                        self.status_update.emit(f"Detected {self.filename}...")
                        try:
                            shutil.copy2(src_file, dst_file)
                            if self.mode == "move":
                                os.remove(src_file)
                                action = "Moved"
                            else:
                                action = "Copied"
                            self.file_moved.emit("File Transferred", f"{action} {self.filename}")
                            self.status_update.emit("Waiting for new file...")
                        except Exception as move_err:
                            self.status_update.emit(f"Transfer failed: {str(move_err)}")
                    else:
                        self.status_update.emit("Writing in progress...")
                
            except Exception as e:
                self.status_update.emit(f"Error: {str(e)}")
            
            for _ in range(self.check_interval):
                if not self.running: break
                time.sleep(1)

    def is_file_stable(self, filepath):
        try:
            os.rename(filepath, filepath)
            return True
        except OSError:
            return False

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Auto File Mover")
        self.resize(620, 580)
        
        # Apply Stylesheet
        self.setStyleSheet(STYLESHEET)

        # Config Data Container
        self.config_data = {
            "presets": {},
            "last_state": {
                "src": "",
                "dst": "",
                "file": "",
                "sound": True,
                "interval": 3,
                "mode": "move"
            },
            "settings": {
                "custom_sound": ""
            }
        }
        
        # Init Worker
        self.worker = FileMoverWorker()
        self.worker.status_update.connect(self.update_status_label)
        self.worker.file_moved.connect(self.on_transfer_success)

        # UI & Tray
        self.init_ui()
        self.init_tray()
        
        # Load Data from JSON
        self.load_config_file()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)

        # --- HEADER ---
        header_layout = QHBoxLayout()
        title_label = QLabel("Auto File Mover")
        title_label.setObjectName("HeaderTitle")

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        # --- MAIN CARD ---
        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 25, 20, 25)
        card_layout.setSpacing(20)

        # 1. Target File
        card_layout.addWidget(self.create_section_label("File To Watch"))
        file_row = QHBoxLayout()
        self.file_input = QLineEdit()
        self.file_input.setPlaceholderText("Select file...")
        self.file_input.textChanged.connect(self.save_last_state)

        file_btn = QPushButton("Select File...")
        file_btn.setObjectName("PrimaryBtn")
        file_btn.setFixedWidth(110)
        file_btn.clicked.connect(self.smart_browse_file)

        file_row.addWidget(self.file_input, 1)
        file_row.addWidget(file_btn)
        card_layout.addLayout(file_row)

        # 2. Source Folder
        card_layout.addWidget(self.create_section_label("Source Folder"))
        src_row = QHBoxLayout()
        self.src_input = QLineEdit()
        self.src_input.setPlaceholderText("Select folder...")
        self.src_input.textChanged.connect(self.save_last_state)

        src_btn = QPushButton("Browse")
        src_btn.setFixedWidth(110)
        src_btn.clicked.connect(lambda: self.browse_folder(self.src_input))

        src_row.addWidget(self.src_input, 1)
        src_row.addWidget(src_btn)
        card_layout.addLayout(src_row)

        # 3. Destination Folder
        card_layout.addWidget(self.create_section_label("Destination Folder"))
        dst_row = QHBoxLayout()
        self.dst_input = QLineEdit()
        self.dst_input.setPlaceholderText("Select folder...")
        self.dst_input.textChanged.connect(self.save_last_state)

        dst_btn = QPushButton("Browse")
        dst_btn.setFixedWidth(110)
        dst_btn.clicked.connect(lambda: self.browse_folder(self.dst_input))

        dst_row.addWidget(self.dst_input, 1)
        dst_row.addWidget(dst_btn)
        card_layout.addLayout(dst_row)

        main_layout.addWidget(card)

        # --- SETTINGS ROW ---
        settings_layout = QHBoxLayout()
        settings_layout.setContentsMargins(5, 0, 5, 0)

        # Mode selection (Copy or Move)
        self.mode_button_group = QButtonGroup(self)
        self.copy_radio = QRadioButton("Copy")
        self.move_radio = QRadioButton("Move")
        self.move_radio.setChecked(True)  # Default to Move
        self.mode_button_group.addButton(self.copy_radio)
        self.mode_button_group.addButton(self.move_radio)
        self.copy_radio.toggled.connect(self.save_last_state)

        settings_layout.addWidget(self.copy_radio)
        settings_layout.addWidget(self.move_radio)
        settings_layout.addSpacing(20)

        self.sound_check = QCheckBox("Sound Alert")
        self.sound_check.stateChanged.connect(self.save_last_state)

        self.interval_combo = QComboBox()
        self.interval_combo.setEditable(True)
        self.interval_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.interval_combo.setFixedWidth(120)
        # Add predefined intervals (stored in seconds)
        self.interval_combo.addItem("1s", 1)
        self.interval_combo.addItem("3s", 3)
        self.interval_combo.addItem("5s", 5)
        self.interval_combo.addItem("10s", 10)
        self.interval_combo.addItem("15s", 15)
        self.interval_combo.addItem("30s", 30)
        self.interval_combo.addItem("60s", 60)
        self.interval_combo.addItem("5 mins", 300)
        self.interval_combo.addItem("10 mins", 600)
        self.interval_combo.addItem("15 mins", 900)
        self.interval_combo.addItem("30 mins", 1800)
        self.interval_combo.addItem("60 mins", 3600)
        self.interval_combo.setCurrentIndex(1)  # Default to 3s
        self.interval_combo.currentIndexChanged.connect(self.save_last_state)
        self.interval_combo.lineEdit().editingFinished.connect(self.on_interval_manual_entry)

        settings_layout.addWidget(self.sound_check)
        settings_layout.addStretch()
        settings_layout.addWidget(QLabel("Check Interval:"))
        settings_layout.addWidget(self.interval_combo)

        main_layout.addLayout(settings_layout)

        # --- PRESETS BAR ---
        preset_layout = QHBoxLayout()
        preset_layout.setSpacing(10)

        self.preset_combo = QComboBox()
        self.preset_combo.setView(QListView())
        self.preset_combo.setPlaceholderText("Select Preset...")
        self.preset_combo.setMinimumWidth(220)
        self.preset_combo.currentIndexChanged.connect(self.apply_preset)

        save_preset_btn = QPushButton("Save")
        save_preset_btn.clicked.connect(self.save_new_preset)

        del_preset_btn = QPushButton("Delete")
        del_preset_btn.clicked.connect(self.delete_preset)

        preset_layout.addWidget(QLabel("Preset:"))
        preset_layout.addWidget(self.preset_combo, 1)
        preset_layout.addWidget(save_preset_btn)
        preset_layout.addWidget(del_preset_btn)
        main_layout.addLayout(preset_layout)

        # --- ACTION BUTTON ---
        btn_container = QWidget()
        btn_layout = QVBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 10, 0, 0)
        
        self.toggle_btn = QPushButton("START MONITORING")
        self.toggle_btn.setObjectName("StartBtn")
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.clicked.connect(self.toggle_monitoring)
        
        btn_layout.addWidget(self.toggle_btn)
        main_layout.addWidget(btn_container)

    def create_section_label(self, text):
        lbl = QLabel(text)
        lbl.setObjectName("SectionLabel")
        return lbl

    def init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        icon = self.style().standardIcon(self.style().StandardPixmap.SP_DriveFDIcon)
        self.tray_icon.setIcon(icon)

        tray_menu = QMenu()

        # Add title (clickable - opens dashboard)
        title_action = QAction("Auto File Mover", self)
        title_font = QFont()
        title_font.setBold(True)
        title_action.setFont(title_font)
        title_action.triggered.connect(self.show_window)
        tray_menu.addAction(title_action)

        # Add separator
        tray_menu.addSeparator()

        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.show_settings)
        tray_menu.addAction(settings_action)

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit_app)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        self.tray_icon.activated.connect(self.on_tray_click)

    def show_settings(self):
        """Show settings dialog for custom sound file."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Settings")
        dialog.setMinimumWidth(500)
        dialog.setStyleSheet(STYLESHEET)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Sound settings section
        sound_label = QLabel("NOTIFICATION SOUND")
        sound_label.setObjectName("SectionLabel")
        layout.addWidget(sound_label)

        sound_row = QHBoxLayout()
        self.sound_path_input = QLineEdit()
        self.sound_path_input.setPlaceholderText("Default system sound (leave empty for default)")
        self.sound_path_input.setText(self.config_data.get("settings", {}).get("custom_sound", ""))

        browse_sound_btn = QPushButton("Browse...")
        browse_sound_btn.clicked.connect(self.browse_sound_file)

        clear_sound_btn = QPushButton("Clear")
        clear_sound_btn.clicked.connect(self.clear_custom_sound)

        sound_row.addWidget(self.sound_path_input, 1)
        sound_row.addWidget(browse_sound_btn)
        sound_row.addWidget(clear_sound_btn)
        layout.addLayout(sound_row)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(lambda: self.save_settings(dialog))
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.exec()

    def browse_sound_file(self):
        """Browse for a sound file."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Sound File (will play max 5 seconds)",
            "",
            "Sound Files (*.wav *.mp3 *.ogg *.flac *.m4a *.aac);;All Files (*.*)"
        )
        if path:
            self.sound_path_input.setText(path)

    def clear_custom_sound(self):
        """Clear the custom notification sound."""
        self.sound_path_input.clear()

    def save_settings(self, dialog):
        """Save settings and close dialog."""
        if "settings" not in self.config_data:
            self.config_data["settings"] = {}
        self.config_data["settings"]["custom_sound"] = self.sound_path_input.text()
        self.write_config_file()
        dialog.accept()

    # --- JSON CONFIGURATION HANDLING ---
    def load_config_file(self):
        """Loads presets and last state from JSON file next to script."""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                    # Merge loaded data with defaults to prevent key errors if new keys are added later
                    if "presets" in loaded_data:
                        self.config_data["presets"] = loaded_data["presets"]
                    if "last_state" in loaded_data:
                        self.config_data["last_state"].update(loaded_data["last_state"])
            except Exception as e:
                print(f"Error loading config: {e}")
        
        # Apply the loaded data to UI
        self.update_preset_combo()

        last = self.config_data["last_state"]
        self.src_input.setText(last.get("src", ""))
        self.dst_input.setText(last.get("dst", ""))
        self.file_input.setText(last.get("file", ""))
        self.sound_check.setChecked(last.get("sound", True))
        self.set_interval_value(last.get("interval", 3))

        # Set mode (copy or move)
        mode = last.get("mode", "move")
        if mode == "copy":
            self.copy_radio.setChecked(True)
        else:
            self.move_radio.setChecked(True)

    def write_config_file(self):
        """Writes current config_data to JSON."""
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    # --- UI LOGIC ---

    def toggle_monitoring(self, checked):
        if checked:
            if not all([self.src_input.text(), self.dst_input.text(), self.file_input.text()]):
                self.toggle_btn.setChecked(False)
                QMessageBox.warning(self, "Missing Info", "Please define Source, Destination, and Filename.")
                return

            self.toggle_btn.setText("STOP MONITORING")
            self.toggle_btn.setObjectName("StopBtn")
            self.toggle_btn.style().unpolish(self.toggle_btn)
            self.toggle_btn.style().polish(self.toggle_btn)
            
            self.set_inputs_enabled(False)

            self.worker.set_params(
                self.src_input.text(),
                self.dst_input.text(),
                self.file_input.text(),
                self.get_interval_value(),
                "move" if self.move_radio.isChecked() else "copy"
            )
            self.worker.start()
            self.save_last_state()
            
        else:
            self.worker.running = False
            self.worker.wait()
            
            self.toggle_btn.setText("START MONITORING")
            self.toggle_btn.setObjectName("StartBtn")
            self.toggle_btn.style().unpolish(self.toggle_btn)
            self.toggle_btn.style().polish(self.toggle_btn)

            self.set_inputs_enabled(True)

    def set_inputs_enabled(self, enabled):
        self.src_input.setEnabled(enabled)
        self.dst_input.setEnabled(enabled)
        self.file_input.setEnabled(enabled)
        self.preset_combo.setEnabled(enabled)
        self.interval_combo.setEnabled(enabled)
        self.copy_radio.setEnabled(enabled)
        self.move_radio.setEnabled(enabled)

    # --- PRESETS ---
    def update_preset_combo(self):
        self.preset_combo.blockSignals(True)
        self.preset_combo.clear()
        self.preset_combo.addItem("", None)
        for name in sorted(self.config_data["presets"].keys()):
            self.preset_combo.addItem(name, name)
        self.preset_combo.blockSignals(False)

    def save_new_preset(self):
        if not all([self.src_input.text(), self.dst_input.text(), self.file_input.text()]):
            QMessageBox.warning(self, "Error", "Fill in fields first.")
            return

        name, ok = QInputDialog.getText(self, "Save Preset", "Preset Name:")
        if ok and name:
            data = {
                "src": self.src_input.text(),
                "dst": self.dst_input.text(),
                "file": self.file_input.text(),
                "mode": "move" if self.move_radio.isChecked() else "copy"
            }
            self.config_data["presets"][name] = data
            self.write_config_file()
            self.update_preset_combo()
            self.preset_combo.setCurrentText(name)

    def delete_preset(self):
        current_name = self.preset_combo.currentText()
        if current_name in self.config_data["presets"]:
            del self.config_data["presets"][current_name]
            self.write_config_file()
            self.update_preset_combo()
            self.src_input.clear()
            self.dst_input.clear()
            self.file_input.clear()

    def apply_preset(self):
        name = self.preset_combo.currentText()
        if name in self.config_data["presets"]:
            if self.toggle_btn.isChecked():
                QMessageBox.warning(self, "Busy", "Stop monitoring before changing presets.")
                return

            data = self.config_data["presets"][name]
            self.src_input.setText(data.get("src", ""))
            self.dst_input.setText(data.get("dst", ""))
            self.file_input.setText(data.get("file", ""))

            # Restore mode setting
            mode = data.get("mode", "move")
            if mode == "copy":
                self.copy_radio.setChecked(True)
            else:
                self.move_radio.setChecked(True)

            self.save_last_state() # Save immediately so if app closes it remembers

    def save_last_state(self):
        """Called whenever inputs change to keep JSON up to date."""
        self.config_data["last_state"] = {
            "src": self.src_input.text(),
            "dst": self.dst_input.text(),
            "file": self.file_input.text(),
            "sound": self.sound_check.isChecked(),
            "interval": self.get_interval_value(),
            "mode": "move" if self.move_radio.isChecked() else "copy"
        }
        self.write_config_file()

    # --- HELPERS ---
    def get_interval_value(self):
        """Get the current interval value in seconds."""
        current_data = self.interval_combo.currentData()
        if current_data is not None:
            return current_data
        # If manually entered, parse the text
        text = self.interval_combo.currentText().strip()
        return self.parse_interval_text(text)

    def set_interval_value(self, seconds):
        """Set the interval combo to show the given number of seconds."""
        # Try to find matching preset
        for i in range(self.interval_combo.count()):
            if self.interval_combo.itemData(i) == seconds:
                self.interval_combo.setCurrentIndex(i)
                return
        # If no match, set custom text
        self.interval_combo.setCurrentText(self.format_interval(seconds))

    def parse_interval_text(self, text):
        """Parse interval text like '5s', '10 mins', or just '30' into seconds."""
        text = text.lower().strip()
        if not text:
            return 3  # Default

        # Extract number
        import re
        match = re.search(r'(\d+)', text)
        if not match:
            return 3

        value = int(match.group(1))

        # Check for time unit
        if 'min' in text:
            return value * 60
        elif 'h' in text or 'hr' in text:
            return value * 3600
        else:  # Default to seconds
            return value

    def format_interval(self, seconds):
        """Format seconds into readable text."""
        if seconds >= 3600:
            mins = seconds // 60
            if mins >= 60:
                return f"{mins // 60} hrs"
            return f"{mins} mins"
        elif seconds >= 60:
            return f"{seconds // 60} mins"
        else:
            return f"{seconds}s"

    def on_interval_manual_entry(self):
        """Handle manual text entry in the interval combo."""
        text = self.interval_combo.currentText().strip()
        seconds = self.parse_interval_text(text)
        # Update the display to normalized format
        self.interval_combo.setCurrentText(self.format_interval(seconds))
        self.save_last_state()

    def browse_folder(self, line_edit):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            line_edit.setText(folder)

    def smart_browse_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select File to Monitor")
        if path:
            directory = os.path.dirname(path)
            filename = os.path.basename(path)
            self.file_input.setText(filename)
            self.src_input.setText(directory)

    def on_transfer_success(self, title, message):
        self.tray_icon.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 2000)
        if self.sound_check.isChecked():
            self.play_notification_sound()

    def play_notification_sound(self):
        """Play notification sound (custom or default), max 5 seconds."""
        custom_sound = self.config_data.get("settings", {}).get("custom_sound", "")

        if custom_sound and os.path.exists(custom_sound):
            try:
                import subprocess
                import threading

                def play_with_timeout(sound_path):
                    """Play sound and kill after 5 seconds."""
                    try:
                        if platform.system() == "Windows":
                            # Windows: try winsound for WAV, stop after 5 seconds
                            if sound_path.lower().endswith('.wav'):
                                winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                                time.sleep(5)
                                winsound.PlaySound(None, winsound.SND_PURGE)
                            else:
                                # Non-WAV: use default
                                self.play_default_sound()
                        elif platform.system() == "Darwin":  # macOS
                            proc = subprocess.Popen(["afplay", sound_path],
                                                  stderr=subprocess.DEVNULL)
                            proc.wait(timeout=5)
                        else:  # Linux
                            # Try common audio players with 5-second timeout
                            for player in ["paplay", "aplay"]:
                                try:
                                    proc = subprocess.Popen([player, sound_path],
                                                          stderr=subprocess.DEVNULL,
                                                          stdout=subprocess.DEVNULL)
                                    proc.wait(timeout=5)
                                    break
                                except FileNotFoundError:
                                    continue
                    except subprocess.TimeoutExpired:
                        proc.kill()  # Kill if still playing after 5 seconds
                    except Exception as e:
                        logging.warning(f"Error playing sound: {e}")

                # Play in background thread
                threading.Thread(target=play_with_timeout, args=(custom_sound,), daemon=True).start()

            except Exception as e:
                logging.warning(f"Could not play custom sound: {e}")
                self.play_default_sound()
        else:
            self.play_default_sound()

    def play_default_sound(self):
        """Play default system notification sound."""
        if platform.system() == "Windows":
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        else:
            QApplication.beep()

    def update_status_label(self, text):
        # Status updates from worker (currently not displayed in UI)
        pass

    def on_tray_click(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_window()

    def show_window(self):
        self.show()
        self.activateWindow()
        self.raise_()

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray_icon.showMessage("Auto File Mover", "Running in background.", QSystemTrayIcon.MessageIcon.Information, 1000)

    def quit_app(self):
        self.worker.running = False
        QApplication.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion") 
    app.setQuitOnLastWindowClosed(False)
    
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())