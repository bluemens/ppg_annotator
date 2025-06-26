import sys
import os
import numpy as np
import pandas as pd
import requests
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout,
                             QWidget, QFileDialog, QLabel, QHBoxLayout, QSlider, 
                             QInputDialog, QComboBox, QMessageBox, 
                             QDialog, QLineEdit, QFormLayout, QDialogButtonBox)
from PyQt5.QtCore import Qt, QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtCore import QEvent

from annotatorkit import config

"""
This is our GUI for manual annotation. The annotator has many functions. You can load
the signal as a parquet file which is then 
"""

SAMPLE_RATE = 125
PPG_SIGNAL_COLUMN_NAME_1 = '8032_PPG_00' 
PPG_SIGNAL_COLUMN_NAME_2 = 'TAG_8032_PPG_00'
WINDOW_HEIGHT = 30000
OVERLAP = 0.5
WINDOW_WIDTH = 5 #seconds
SEGMENT_LENGTH = WINDOW_WIDTH * SAMPLE_RATE

BASE_URL = "http://127.0.0.1:8000"

def get_config_from_user(defaults):
    dialog = QDialog()
    dialog.setWindowTitle("Annotator Configuration")

    annotator_input = QLineEdit(defaults["annotator_id"])
    url_input = QLineEdit(defaults["base_url"])

    form = QFormLayout(dialog)
    form.addRow("Annotator ID:", annotator_input)
    form.addRow("Backend URL:", url_input)

    buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    form.addWidget(buttons)

    if dialog.exec_() == QDialog.Accepted:
        return {
            "annotator_id": annotator_input.text().strip(),
            "base_url": url_input.text().strip()
        }
    else:
        return None
class Annotator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PPG Signal Annotator")
        self.resize(1000, 600)

        # Load and show config dialog
        defaults = config.load_config()
        user_config = get_config_from_user(defaults)

        if not user_config:
            sys.exit()

        # Validate annotator ID
        try:
            response = requests.get(f"{user_config['base_url']}/validate_annotator/{user_config['annotator_id']}")
            if response.status_code != 200:
                QMessageBox.critical(self, "Access Denied", "Invalid annotator ID. The application will now close.")
                sys.exit()
        except Exception as e:
            QMessageBox.critical(self, "Network Error", f"Could not contact server:\n{e}")
            sys.exit()

        # Save validated config and store values
        config.save_config(user_config)
        self.annotator_id = user_config["annotator_id"]
        self.base_url = user_config["base_url"]

        # Remaining attributes
        self.segment_length = SEGMENT_LENGTH
        self.overlap = 0.5
        self.current_index = 0
        self.signals = None
        self.timestamps = None
        self.labels = []
        self.label_df = None
        self.last_label_path = None

        self.initUI()

    def initUI(self):
        self.setFocusPolicy(Qt.StrongFocus)
        self.canvas = FigureCanvas(Figure(figsize=(10, 4)))
        self.ax = self.canvas.figure.subplots()
        self.installEventFilter(self)

        #loads complete ppg signal
        # load_signal_btn = QPushButton("Load Signal")
        # load_signal_btn.clicked.connect(self.load_signal)

        #dropdown menu

        self.signal_dropdown = QComboBox()
        self.signal_dropdown.currentTextChanged.connect(self.handle_signal_selection)

        load_labels_btn = QPushButton("Load Label File")
        load_labels_btn.clicked.connect(self.load_labels)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setFixedHeight(40)
        self.slider.setRange(0, 100)
        self.slider.setTickInterval(10)
        self.slider.setValue(50)
        self.slider_label = QLabel("Label: 0.50")
        self.slider_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        self.slider.valueChanged.connect(self.update_slider_label)

        label_btn = QPushButton("Label Segment")
        label_btn.clicked.connect(self.label_segment)

        next_btn = QPushButton("Next")
        next_btn.clicked.connect(self.next_segment)

        prev_btn = QPushButton("Previous")
        prev_btn.clicked.connect(self.prev_segment)

        save_btn = QPushButton("Save Labels")
        save_btn.clicked.connect(self.save_labels)

        self.status_label = QLabel("No file loaded")
        self.labeled = QLabel("No label filel loaded")

        layout = QVBoxLayout()
        layout.addWidget(self.canvas)

        controls = QHBoxLayout()
        # controls.addWidget(load_signal_btn)
        controls.addWidget(self.signal_dropdown)
        controls.addWidget(load_labels_btn)
        controls.addWidget(prev_btn)
        controls.addWidget(next_btn)
        controls.addWidget(self.slider_label)
        controls.addWidget(self.slider)
        controls.addWidget(label_btn)
        controls.addWidget(save_btn)

        layout.addLayout(controls)
        layout.addWidget(self.labeled)
        layout.addWidget(self.status_label)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.fetch_signals_from_backend()
  
    def handle_signal_selection(self, signal_id):
        if not signal_id:
            return
        try:
            response = requests.get(f"{BASE_URL}/load_signal/{signal_id}/{self.annotator_id}")
            records = response.json()
            df = pd.DataFrame(records)
            self.current_signal_id = signal_id
            self.timestamps = df["TIMESTAMP"].values if "TIMESTAMP" in df else np.arange(len(df))
            try:
                self.signals = df[PPG_SIGNAL_COLUMN_NAME_1].values
            except:
                self.signals = df[PPG_SIGNAL_COLUMN_NAME_2].values  # put ppg column name into this

            self.status_label.setText(f"Loaded signal {signal_id}")

            self.current_index = 0
            self.labels.clear()
            self.update_plot()

        except Exception as e:
            self.status_label.setText(f"Failed to load signal {signal_id}: {e}")
  
    def fetch_signals_from_backend(self):
        try:
            response = requests.get(f"{BASE_URL}/signals")
            signal_list = response.json().get("signals", [])
            self.signal_dropdown.clear()
            for signal in signal_list:
                self.signal_dropdown.addItem(signal["id"])  # assuming 'id' is the signal name
        except Exception as e:
            self.status_label.setText(f"Error fetching signals: {e}")


    def eventFilter(self, source, event):
        if event.type() == QEvent.KeyPress:
            self.keyPressEvent(event)
            return True  # Stop event from propagating
        return super().eventFilter(source, event)
    
    def update_slider_label(self):
        value = self.slider.value() / 100.0
        self.slider_label.setText(f"Label: {value:.2f}")

    def load_signal(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Signal File", "", "Parquet Files (*.parquet)")
        if file_path:
            df = pd.read_parquet(file_path)
            self.timestamps = df["TIMESTAMP"].values if "TIMESTAMP" in df else np.arange(len(df))
            try:
                self.signals = df[PPG_SIGNAL_COLUMN_NAME_1].values
            except:
                self.signals = df[PPG_SIGNAL_COLUMN_NAME_2].values  # put ppg column name into this
            self.labels.clear()
            self.current_index = 0
            self.update_plot()
            self.status_label.setText(f"Loaded {file_path}")

    def load_labels(self):
        #Load Label
        response = requests.get(f"{BASE_URL}/get_annotations/{self.annotator_id}/{self.current_signal_id}")
        user_labels = response.json()

        if response.status_code == 200:
            user_labels = response.json()
        else:
            user_labels = []  # No annotations found or error occurred

        self.labels = user_labels

        if user_labels:
            last_segment = max(label["segment_index"] for label in user_labels)
            self.current_index = last_segment + 1
        else:
            self.current_index = 0

        self.update_plot()

    def get_current_segment(self):
        stride = int(self.segment_length * (1 - self.overlap))
        start = self.current_index * stride
        end = start + self.segment_length
        return self.timestamps[start:end], self.signals[start:end], start, end

    def update_plot(self):
        t, y, start, end = self.get_current_segment()
        
        self.ax.clear()
        # y_center = np.mean(y)
        # window_height = WINDOW_HEIGHT 
        # self.ax.set_ylim(y_center - window_height / 2, y_center + window_height / 2)
        self.ax.plot(t, y)

        # Check if current segment already labeled and annotate
        existing_label = None
        existing_confidence = None
        for entry in self.labels:
            if entry['segment_index'] == self.current_index:
                existing_label = entry['snorkel_label']
                existing_confidence = entry['snorkel_confidence']
                break

        if existing_label is not None:
            self.ax.text(0.95, 0.9, f"Existing Label: {existing_label:.2f}",
                         horizontalalignment='right', verticalalignment='center',
                         transform=self.ax.transAxes, fontsize=12, color='red')
        if existing_confidence is not None:
            self.ax.text(0.95, 0.85, f"Existing Confidence: {existing_confidence:.2f}",
                         horizontalalignment='right', verticalalignment='center',
                         transform=self.ax.transAxes, fontsize=12, color='red')
            
        self.ax.set_title(f"Segment {self.current_index} ({start} to {end})")
        self.canvas.draw()

    def label_segment(self):
        _, _, start, end = self.get_current_segment()
        label = self.slider.value() / 100.0
        # Remove any existing label for this segment
        self.labels = [entry for entry in self.labels if entry['segment_index'] != self.current_index]

        self.labels.append({
            "segment_index": self.current_index,
            "start": start,
            "end": end,
            "snorkel_label": label,
            "snorkel_confidence": 1.0, 
            "annotator_id": self.annotator_id
        })

        payload = {
            "annotator_id": self.annotator_id, 
            "signal_id": self.current_signal_id, 
            "annotations": self.labels
        }
        response = requests.post(f"{BASE_URL}/upload_annotations", json=payload)
        self.labeled.setText(f"Segment {self.current_index} labeled as {label:.2f}")
        self.labeled.setStyleSheet("color: green; font-weight: bold; font-size: 40px")
        QTimer.singleShot(2000, lambda: self.labeled.setStyleSheet(""))
        self.update_plot()

    def next_segment(self):
        max_index = int((len(self.signals) - self.segment_length) / (self.segment_length * (1 - self.overlap)))
        if self.current_index < max_index:
            self.current_index += 1
            self.update_plot()

        self.status_label.setText(f"Segment {self.current_index}/{max_index}")
        self.status_label.setStyleSheet("color: blue; font-weight: bold")

    def prev_segment(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.update_plot()
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            self.label_segment()
        
        if event.key() == Qt.Key_A:
            self.prev_segment()
        elif event.key() == Qt.Key_D:
            self.next_segment()
        elif event.key() == Qt.Key_Left:
            value = max(0, self.slider.value() - 16)
            self.slider.setValue(value)
        elif event.key() == Qt.Key_Right:
            value = min(100, self.slider.value() + 16)
            self.slider.setValue(value)
        elif event.key() == Qt.Key_Down:
            value = max(0, self.slider.value() - 1)
            self.slider.setValue(value)
        elif event.key() == Qt.Key_Up:
            value = min(100, self.slider.value() + 1)
            self.slider.setValue(value)
        elif event.key() == Qt.Key_0:
            value = 0
            self.slider.setValue(value)
            self.label_segment()
            self.next_segment()
        elif event.key() == Qt.Key_1:
            value = 25
            self.slider.setValue(value)
            self.label_segment() 
            self.next_segment()
        elif event.key() == Qt.Key_2:
            value = 42
            self.slider.setValue(value)
            self.label_segment()
            self.next_segment()
        elif event.key() == Qt.Key_3:
            value = 59
            self.slider.setValue(value)
            self.label_segment()
            self.next_segment()
        elif event.key() == Qt.Key_4:
            value = 76
            self.slider.setValue(value)
            self.label_segment()
            self.next_segment()
        elif event.key() == Qt.Key_5:
            value = 93
            self.slider.setValue(value)
            self.label_segment()
            self.next_segment()
        elif event.key() == Qt.Key_9:
            value = 100
            self.slider.setValue(value)
            self.label_segment()
            self.next_segment()
 
           


    def save_labels(self):
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save Label File", "", "Parquet Files (*.parquet)")
        if save_path:
            pd.DataFrame(self.labels).to_parquet(save_path, index=False)
            self.status_label.setText(f"Saved labels to {save_path}")

def run_app():
    app = QApplication(sys.argv)
    window = Annotator()
    window.show()
    sys.exit(app.exec_())
