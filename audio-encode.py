import sys
import wave
import base64
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QMessageBox, QFileDialog, QProgressBar, QLabel
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon
from tqdm import tqdm

class Worker(QThread):
    finished = pyqtSignal()
    progressUpdated = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.file_path = ""

    def encode(self):
        try:
            with open(self.file_path, 'rb') as f:
                data = f.read()
                encoded_data = base64.b64encode(data)
            decoded_text = encoded_data.decode('utf-8')

            binary_string = ''.join(format(ord(char), '08b') for char in decoded_text)

            output_file, _ = QFileDialog.getSaveFileName(None, "Save Audio File", "encoded.wav", "WAV files (*.wav)")
            if output_file:
                bytes_data = bytes(int(binary_string[i:i+8], 2) for i in range(0, len(binary_string), 8))
                with wave.open(output_file, 'wb') as wave_file:
                    wave_file.setnchannels(1)
                    wave_file.setsampwidth(1)
                    wave_file.setframerate(44100)
                    total_bytes = len(bytes_data)
                    bytes_written = 0
                    with tqdm(total=total_bytes, unit='B', unit_scale=True, desc='Writing audio') as pbar:
                        for i in range(0, len(bytes_data), 1024):
                            chunk = bytes_data[i:i+1024]
                            wave_file.writeframes(chunk)
                            bytes_written += len(chunk)
                            pbar.update(len(chunk))
                            progress = bytes_written * 100 // total_bytes
                            self.progressUpdated.emit(progress)

                QMessageBox.information(None, "Success", "Text encoded and saved as encoded.wav")
        except Exception as e:
            QMessageBox.critical(None, "Error", str(e))
        finally:
            self.finished.emit()

    def decode(self):
        try:
            binary_data = audio_to_binary(self.file_path)
            decoded_text = binary_to_text(binary_data)
            output_file, _ = QFileDialog.getSaveFileName(None, "Save Text File", "output.zip", "ZIP files (*.zip)")
            if output_file:
                with open(output_file, 'wb') as f:
                    decoded_data = base64.b64decode(decoded_text)
                    f.write(decoded_data)
                QMessageBox.information(None, "Success", "Audio decoded and saved as output.zip")
        except Exception as e:
            QMessageBox.critical(None, "Error", str(e))
        finally:
            self.finished.emit()

class BinaryConverter(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("CLOUD STORAGE")
        self.setGeometry(100, 100, 500, 250)
        self.setStyleSheet("background-color: #2b3438; color: white;")
        self.setWindowIcon(QIcon('icon.jpg'))

        self.encode_button = QPushButton("Encode FILE", self)
        self.encode_button.setGeometry(50, 50, 150, 40)
        self.encode_button.setStyleSheet("background-color: #00FFFF; color: black; border-radius: 20px;")
        self.encode_button.clicked.connect(self.encode_and_convert)

        self.decode_button = QPushButton("Decode FILE", self)
        self.decode_button.setGeometry(200, 50, 150, 40)
        self.decode_button.setStyleSheet("background-color: #a056bf; color: white; border-radius: 20px;")
        self.decode_button.clicked.connect(self.decode_and_convert)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setGeometry(50, 160, 400, 20)

        self.credit_label = QLabel(self)
        self.credit_label.setGeometry(350, 20, 150, 20)
        self.credit_label.setText("Use at your own risk")
        self.credit_label.setStyleSheet("color: white;")

        self.worker = Worker()
        self.worker.moveToThread(QApplication.instance().thread())

        self.worker.progressUpdated.connect(self.update_progress)

    def encode_and_convert(self):
        self.progress_bar.setValue(0)
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File")
        if file_path:
            self.worker.file_path = file_path
            QTimer.singleShot(0, self.worker.encode)

    def decode_and_convert(self):
        self.progress_bar.setValue(0)
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File")
        if file_path:
            self.worker.file_path = file_path
            QTimer.singleShot(0, self.worker.decode)

    def update_progress(self, value):
        self.progress_bar.setValue(value)

def audio_to_binary(input_file):
    with wave.open(input_file, 'rb') as wave_file:
        frames = wave_file.readframes(wave_file.getnframes())
        binary_string = ''.join(format(byte, '08b') for byte in frames)
        return binary_string

def binary_to_text(binary_string):
    text = ''.join(chr(int(binary_string[i:i+8], 2)) for i in range(0, len(binary_string), 8))
    return text

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = BinaryConverter()
    window.show()

    sys.exit(app.exec_())
