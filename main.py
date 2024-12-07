from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QSlider, QLabel, QComboBox, QWidget, QGridLayout
from PyQt5.QtWidgets import QFrame
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel, QComboBox, QSlider, QHBoxLayout
from PyQt5 import QtCore
from PyQt5.QtWidgets import QLabel, QFileDialog, QComboBox, QGridLayout, QApplication, QWidget
from PyQt5.QtGui import QPixmap
from PyQt5 import QtCore
import sys
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QComboBox, QSlider, QWidget, QHBoxLayout
from PyQt5 import QtCore
import numpy as np
from PyQt5.QtGui import QPixmap, QImage, QPainter, QColor, QPen
from PIL import Image, ImageQt
from PyQt5.QtCore import Qt, QRect, QObject, pyqtSignal, QPoint


class SelectionManager(QObject):
    selection_changed = pyqtSignal(QRect)  # Signal to notify when selection changes

    def __init__(self):
        super().__init__()
        self.start_point = None
        self.end_point = None

    def set_selection(self, start_point: QPoint, end_point: QPoint):
        self.start_point = start_point
        self.end_point = end_point
        rect = QRect(start_point, end_point).normalized()
        self.selection_changed.emit(rect)

class ImageLabel(QLabel):
    def __init__(self, selection_manager: SelectionManager, parent=None):
        super().__init__(parent)
        self.selection_manager = selection_manager
        self.selection_manager.selection_changed.connect(self.update_selection)
        self.start_point = None
        self.end_point = None
        self.selection_rect = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Start drawing rectangle
            self.start_point = event.pos()
            self.end_point = self.start_point
            self.update()

    def mouseMoveEvent(self, event):
        if self.start_point is not None:
            # Update rectangle during dragging
            self.end_point = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Finalize rectangle
            self.end_point = event.pos()
            self.selection_rect = QRect(self.start_point, self.end_point).normalized()
            self.selection_manager.set_selection(self.start_point, self.end_point)

    def paintEvent(self, event):
        # Draw the image and rectangle
        super().paintEvent(event)
        if self.selection_rect:
            painter = QPainter(self)
            pen = QPen(QColor("blue"))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawRect(self.selection_rect)

    def update_selection(self, rect: QRect):
        # Update the selection rectangle from the manager
        self.selection_rect = rect
        self.update()
class UI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Mag/Phase")
        self.setGeometry(100, 100, 1200, 700)

        self.dark_theme()
        self.image_labels = []
        self.image_list = {}
        self.image_id = 0
        self.freq_component_combobox = []
        self.freq_component_label =[]
        self.image_phases = [None] * 4
        self.image_magnitudes = [None] * 4
        self.image_real_part = [None] * 4
        self.image_imaginary_part = [None] * 4
        self.weighted_magnitude = [np.zeros((1, 1))] * 4
        self.weighted_phase = [np.zeros((1, 1))] * 4
        self.selected_port_indx = 0
        self.start = 1
        self.output_label = []
        self.sliders = []
        self.mixer_region=[]
        self.selected_port='Port 1'
        self.selected_mixer_region = "Inner"
        self.output_combo = []
        self.output_freq_components1 = "Phase"
        self.output_freq_components2 = "Phase"
        self.output_freq_components3 = "Phase"
        self.output_freq_components4 = "Phase"
        self.combined_magnitude = None
        self.combined_phase = None
        self.start_point = None
        self.end_point = None
        self.selection_rect = None
        self.selection_manager = SelectionManager()






        main_layout = QHBoxLayout()

        left_layout = QVBoxLayout()

        # section 1: input images
        section1_layout = QGridLayout()
        for i in range(4):
            # making 4 image lables
            original_image_label = QLabel(f"Original Image {i + 1}")
            image_label = QLabel(f"Add Image {i + 1}")
            image_label.setFixedSize(400, 250) # 400 is the width, 250 is th eheight
            image_label.setStyleSheet("border: 1px solid #444; background-color: #333; color: white;")
            image_label.setAlignment(QtCore.Qt.AlignCenter)

            image_label.mouseDoubleClickEvent = lambda event, idx=i: self.load_image(idx)
            image_label.setScaledContents(True)

            # Add label to the list
            self.image_labels.append(image_label)

            # Create a combo box
            combo_box = QComboBox()
            combo_box.addItems(["Choose FT Component",'FT Magnitude','FT Phase',"FT Real Components", "FT Imaginary Components"])
            combo_box.setStyleSheet("""
                QComboBox {
                    background-color: #8B0047; 
                    color: #FFFFFF; /* White text for readability */
                    border: 1px solid #555; /* Subtle border for structure */
                    border-radius: 5px; /* Smooth rounded corners */
                    padding: 5px; /* Padding for spacing */
                }
                QComboBox:hover {
                    border: 1px solid #00BFFF; /* Highlight border on hover */
                }

                QComboBox QAbstractItemView {
                    background-color: #2E2E2E; /* Dropdown list background */
                    color: #FFFFFF; /* List item text color */
                    selection-background-color: #00BFFF; /* Highlight selected item */
                    selection-color: #FFFFFF; /* Selected text color */
                    border: 1px solid #555; /* Border for the dropdown */
                }
            """)
            self.freq_component_combobox.append(combo_box)
            combo_box.currentIndexChanged.connect(
                lambda index, combo=combo_box, idx=i: self.show_freq_components(idx, combo.currentText())
            )

            section1_layout.addWidget(original_image_label, 0, i)
            section1_layout.addWidget(image_label, 1, i)
            section1_layout.addWidget(combo_box, 2, i)

        # second_label = self.image_labels[1]
        # second_label.setText("new Text for Second Label")
        # second_label.setStyleSheet("border: 2px solid red; background-color: #555; color: yellow;")

        # Section 2
        section2_layout = QGridLayout()
        for i in range(4):
            ft_label = ImageLabel(self.selection_manager)
            ft_label.setFixedSize(400, 250)  
            ft_label.setStyleSheet("border: 1px solid #444; background-color: #333; color: white;")
            ft_label.setAlignment(QtCore.Qt.AlignCenter)
            section2_layout.addWidget(ft_label, 0, i)
            self.freq_component_label.append(ft_label)
            ft_label.setScaledContents(True)


        # section 3: output images
        section3_layout = QHBoxLayout()
        for i in range(2):
            output_label = QLabel(f"Output {i + 1}")
            output_label.setFixedSize(800, 400)
            output_label.setStyleSheet("border: 1px solid #444; background-color: #333; color: white;")
            output_label.setAlignment(QtCore.Qt.AlignCenter)
            self.output_label.append(output_label)
            section3_layout.addWidget(output_label)


        
        left_layout.addLayout(section1_layout)
        left_layout.addLayout(section2_layout)
        left_layout.addLayout(section3_layout)

        right_layout = QVBoxLayout()

        
        def create_widget(label_text, combo_items,counter):
            # the container for the group
            container = QWidget()
            container_layout = QVBoxLayout()

            # label
            label = QLabel(label_text)
            label.setStyleSheet("color: white; font-size: 14px;")
            container_layout.addWidget(label)

            # slider
            slider = QSlider(QtCore.Qt.Horizontal)
            slider.setRange(0, 100)
            slider.setValue(0)
            slider_value_label = QLabel("0%")
            slider_value_label.setStyleSheet("color: #ffcce6; font-size: 12px; font-weight: bold;")
            slider.valueChanged.connect(lambda value, lbl=slider_value_label: lbl.setText(f"{value}%"))
            slider.setStyleSheet("""
                QSlider::groove:horizontal {
                    height: 6px;
                    background: #F8F8F8; /* Light gray groove */
                    border-radius: 3px; /* Smooth rounded edges */
                }
                QSlider::handle:horizontal {
                    background: #8B0047; /* Deep red for the handle */
                    border: none;
                    width: 20px;
                    height: 20px;
                    margin: -7px 0; /* Centers the handle */
                    border-radius: 10px; /* Circular handle */
                }
                QSlider::handle:horizontal:hover {
                    background: rgba(139, 0, 71, 0.8); /* Transparent red for hover effect */
                    box-shadow: 0px 0px 10px rgba(139, 0, 71, 0.5); /* Glow effect */
                }
                QSlider::sub-page:horizontal {
                    background: #8B0047; /* Deep red for the progress bar */
                    border-radius: 3px;
                }
                QSlider::add-page:horizontal {
                    background: #D3D3D3; /* Light gray for the unfilled portion */
                    border-radius: 3px;
                }
            """)

            self.sliders.append(slider)
            container_layout.addWidget(slider)
            container_layout.addWidget(slider_value_label)

            # combobox
            combobox = QComboBox()
            combobox.addItems(combo_items)
            combobox.setStyleSheet("""
                QComboBox {
                    background-color: #8B0047; 
                    color: #FFFFFF; /* White text for readability */
                    border: 1px solid #555; /* Subtle border for structure */
                    border-radius: 5px; /* Smooth rounded corners */
                    padding: 5px; /* Padding for spacing */
                }
                QComboBox:hover {
                    border: 1px solid #00BFFF; /* Highlight border on hover */
                }
            """)
            self.output_combo.append(combobox)

            container_layout.addWidget(combobox)

            # set layout for the container
            container.setLayout(container_layout)
            return container

        # mixer O/p Section
        mixer_output_combobox = QComboBox()
        mixer_output_combobox.addItems(["Port 1", "Port 2"])
        mixer_output_combobox.currentIndexChanged.connect(
            lambda index, combo=mixer_output_combobox: self.select_port(index, combo.currentText())
        )
        mixer_output_combobox.setStyleSheet("""
                QComboBox {
                    background-color: #8B0047; 
                    color: #FFFFFF; /* White text for readability */
                    border: 1px solid #555; /* Subtle border for structure */
                    border-radius: 5px; /* Smooth rounded corners */
                    padding: 5px; /* Padding for spacing */
                }
                QComboBox:hover {
                    border: 1px solid #00BFFF; /* Highlight border on hover */
                }
            """)

        # create frame for the Mixer Output group
        mixer_output_label = QLabel("Mixer Output")
        mixer_output_label.setStyleSheet("color: white; font-size: 14px;")
        mixer_output_layout = QVBoxLayout()
        mixer_output_layout.addWidget(mixer_output_label)
        mixer_output_layout.addWidget(mixer_output_combobox)
        mixer_output_frame = QWidget()
        mixer_output_frame.setLayout(mixer_output_layout)

        right_layout.addWidget(mixer_output_frame)

        # mixer Region Section
        mixer_region_combobox = QComboBox()
        mixer_region_combobox.addItems(["Inner", "Outer"])
        mixer_region_combobox.setStyleSheet("""
                QComboBox {
                    background-color: #8B0047; 
                    color: #FFFFFF; /* White text for readability */
                    border: 1px solid #555; /* Subtle border for structure */
                    border-radius: 5px; /* Smooth rounded corners */
                    padding: 5px; /* Padding for spacing */
                }
                QComboBox:hover {
                    border: 1px solid #00BFFF; /* Highlight border on hover */
                }
            """)
        self.mixer_region.append(mixer_region_combobox)
        # create frame for the Mixer Region group
        mixer_region_label = QLabel("Mixer Region")
        mixer_region_label.setStyleSheet("color: white; font-size: 14px;")
        mixer_region_layout = QVBoxLayout()
        mixer_region_layout.addWidget(mixer_region_label)
        mixer_region_layout.addWidget(mixer_region_combobox)
        mixer_region_frame = QWidget()
        mixer_region_frame.setLayout(mixer_region_layout)

        right_layout.addWidget(mixer_region_frame)

        
        for i in range(4):  
            combo_items = ["Phase", "Magnitude","Real part","imaginary part"]
            counter = i
            bordered_widget = create_widget(f"Component {i + 1}", combo_items,counter)
            right_layout.addWidget(bordered_widget)


        right_layout.setSpacing(40)  # spacing between elements for clarity
        right_layout.setContentsMargins(10, 10, 10, 10)  
        right_layout.addStretch()  # filling remaining space and ensure a consistent layout
        for index, slider in enumerate(self.sliders):
            slider.valueChanged.connect(lambda value, idx=index: self.change_slider(idx, value))
        for index, mixer in enumerate(self.mixer_region):
            mixer.currentIndexChanged.connect(lambda value=mixer, idx=index: self.change_slider(idx, value))

        for index, freq_combo in enumerate(self.output_combo):
            freq_combo.currentIndexChanged.connect(lambda value=freq_combo, idx=index: self.change_output_freq_components(idx, value))


        main_layout.addLayout(left_layout, 4)  
        main_layout.addLayout(right_layout, 1) 

        # central Widget
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def dark_theme(self):
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(40, 40, 40))
        dark_palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.Base, QColor(30, 30, 30))
        dark_palette.setColor(QPalette.Text, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.Button, QColor(50, 50, 50))
        dark_palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
        self.setPalette(dark_palette)
        self.setStyleSheet("background-color: #282828; color: white; font-family: Arial; font-size: 14px;")

    def load_image(self, label_index):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Select Image", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            image = Image.open(file_path).convert('L')
            image_array = np.array(image)
            self.image_id = label_index
            self.image_list[self.image_id] = image_array
            height, width = image_array.shape
            qimage = QImage( image_array.data , width, height, QImage.Format_Grayscale8)
            pixmap = QPixmap.fromImage(qimage)

            if self.image_id == 0:
                self.image_labels[0].setPixmap(pixmap.scaled(self.image_labels[0].size(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
                magnitude, phase = self.compute_magnitude_and_phase(image_array)
                real,imaginary=self.compute_real_and_imaginary(image_array)
                self.image_magnitudes.insert(0,magnitude)
                self.image_phases.insert(0,phase)
                self.image_real_part.insert(0,real)
                self.image_imaginary_part.insert(0,imaginary)
            elif self.image_id == 1:
                self.image_labels[1].setPixmap(pixmap.scaled(self.image_labels[1].size(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
                magnitude,phase = self.compute_magnitude_and_phase(self.image_list[self.image_id])
                real,imaginary=self.compute_real_and_imaginary(image_array)
                self.image_magnitudes.insert(1,magnitude)
                self.image_phases.insert(1,phase)
                self.image_real_part.insert(1, real)
                self.image_imaginary_part.insert(1, imaginary)
            elif self.image_id == 2:
                self.image_labels[2].setPixmap(pixmap.scaled(self.image_labels[2].size(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
                magnitude,phase = self.compute_magnitude_and_phase(self.image_list[self.image_id])
                real,imaginary=self.compute_real_and_imaginary(image_array)
                self.image_magnitudes.insert(2,magnitude)
                self.image_phases.insert(2,phase)
                self.image_real_part.insert(2, real)
                self.image_imaginary_part.insert(2, imaginary)
            else:
                self.image_labels[3].setPixmap(pixmap.scaled(self.image_labels[3].size(), QtCore.Qt.KeepAspectRatio,
                                                             QtCore.Qt.SmoothTransformation))
                magnitude,phase = self.compute_magnitude_and_phase(self.image_list[self.image_id])
                real,imaginary=self.compute_real_and_imaginary(image_array)
                self.image_magnitudes.insert(3,magnitude)
                self.image_phases.insert(3,phase)
                self.image_real_part.insert(3, real)
                self.image_imaginary_part.insert(3, imaginary)

    def show_freq_components(self, index, value):
        print(index, value)
        if value == 'FT Magnitude':
            print('Entered')
            self.plot_magnitude(self.image_magnitudes[index],index)
        elif value == "FT Phase":
            self.plot_phase(self.image_phases[index],index)
        elif value == "FT Real Components" :
            print("enter real")
            self.plot_real(self.image_real_part[index],index)
        else:
            print("enter imaginary")
            self.plot_imaginary(self.image_imaginary_part[index],index)
    def compute_magnitude_and_phase(self, image_data):
        image_fourier_transform = np.fft.fft2(image_data)
        f_shift = np.fft.fftshift(image_fourier_transform)
        magnitude_spectrum = 20 * np.log(np.abs(f_shift) + 1)
        phase_spectrum = np.angle(f_shift)
        return magnitude_spectrum,phase_spectrum


    def plot_magnitude(self, magnitude_spectrum, index):
        magnitude_spectrum = np.uint8(np.clip(magnitude_spectrum, 0, 255))
        height, width = magnitude_spectrum.shape
        qimage = QImage(magnitude_spectrum.data, width, height, QImage.Format_Grayscale8)
        pixmap = QPixmap.fromImage(qimage)
        self.freq_component_label[index].setPixmap(
            pixmap.scaled(self.freq_component_label[index].size(), QtCore.Qt.KeepAspectRatio,
                          QtCore.Qt.SmoothTransformation))

    def plot_phase(self,phase_spectrum,index):
        phase_spectrum_normalized = np.uint8(np.clip(((phase_spectrum + np.pi) / (2 * np.pi)) * 255, 0, 255))
        height, width = phase_spectrum_normalized.shape
        qimage = QImage(phase_spectrum_normalized.data, width, height, QImage.Format_Grayscale8)
        pixmap = QPixmap.fromImage(qimage)
        self.freq_component_label[index].setPixmap(
            pixmap.scaled(self.freq_component_label[index].size(), QtCore.Qt.KeepAspectRatio,
                          QtCore.Qt.SmoothTransformation))


    def compute_real_and_imaginary(self, image_data):
        # Compute the Fourier Transform
        image_fourier_transform = np.fft.fft2(image_data)
        # Extract the real part of the Fourier Transform
        real_part = np.real(image_fourier_transform)
        imaginary_part = np.imag(image_fourier_transform)
        return real_part ,imaginary_part


    def plot_real(self, real_part, index):
        real_part_normalized = np.uint8(np.clip(real_part, 0, 255))
        height, width = real_part_normalized.shape
        qimage = QImage(real_part_normalized.data, width, height, QImage.Format_Grayscale8)
        # Convert QImage to QPixmap and set it on the label
        pixmap = QPixmap.fromImage(qimage)
        self.freq_component_label[index].setPixmap(
            pixmap.scaled(self.freq_component_label[index].size(), QtCore.Qt.KeepAspectRatio,
                          QtCore.Qt.SmoothTransformation))

    def plot_imaginary(self, imaginary_part, index):
        imaginary_part_normalized = np.uint8(np.clip(imaginary_part, 0, 255))
        height, width = imaginary_part_normalized.shape
        qimage = QImage(imaginary_part_normalized.data, width, height, QImage.Format_Grayscale8)
        pixmap = QPixmap.fromImage(qimage)
        self.freq_component_label[index].setPixmap(
            pixmap.scaled(self.freq_component_label[index].size(), QtCore.Qt.KeepAspectRatio,
                          QtCore.Qt.SmoothTransformation))


    def select_mixer_region(self,index,value):
        self.selected_mixer_region = value
    def select_port(self,index,value):
        self.selected_port = value
        self.selected_port_indx = index

    def change_output_freq_components(self, index, value):
        # Mapping of index to the attribute names
        attribute_names = [
            "output_freq_components1",
            "output_freq_components2",
            "output_freq_components3",
            "output_freq_components4"
        ]

        # Ensure the index is within the valid range
        if 0 <= index < len(attribute_names):
            # Update the corresponding attribute based on value
            setattr(self, attribute_names[index], "Magnitude" if value == 1 else "Phase")
        else:
            print(f"Invalid index: {index}")

        # Debugging output
        print(f"Index: {index}, Value: {value}")

    def reconstruct_and_display_in_label(self, index):
        self.output_label[index].clear()

        # Ensure we have the same number of magnitudes and phases
        num_images = len(self.image_magnitudes)
        self.combined_magnitude = np.zeros_like(self.weighted_magnitude[0])
        self.combined_phase = np.zeros_like(self.weighted_phase[0])

        # Combine all images' magnitudes and phases
        for i in range(num_images):
            self.combined_magnitude += self.weighted_magnitude[i]
            self.combined_phase += self.weighted_phase[i]

        # Normalize the combined magnitude
        combined_magnitude = np.clip(self.combined_magnitude, 0, np.max(self.combined_magnitude))

        # Reconstruct the complex Fourier spectrum
        complex_spectrum = combined_magnitude * np.exp(1j * self.combined_phase)

        # Compute the inverse Fourier transform
        reconstructed_image = np.fft.ifft2(complex_spectrum)
        reconstructed_image = np.real(reconstructed_image)

        # Normalize the image for display
        reconstructed_image -= reconstructed_image.min()
        if reconstructed_image.max() > 0:
            reconstructed_image /= reconstructed_image.max()
        reconstructed_image *= 255  # Scale to 0-255
        reconstructed_image = reconstructed_image.astype(np.uint8)

        # Convert to QImage
        height, width = reconstructed_image.shape
        q_image = QImage(reconstructed_image.tobytes(), width, height, width, QImage.Format_Grayscale8)

        # Display in QLabel
        pixmap = QPixmap.fromImage(q_image)
        self.output_label[index].setPixmap(
            pixmap.scaled(self.output_label[index].size(), QtCore.Qt.KeepAspectRatio,
                          QtCore.Qt.SmoothTransformation))
        self.output_label[index].setAlignment(Qt.AlignCenter)



    def compute_fft(self,image):
        """Compute the FFT of an image and return magnitude and phase."""
        f = np.fft.fft2(image)
        f_shift = np.fft.fftshift(f)
        magnitude = np.abs(f_shift)
        phase = np.angle(f_shift)
        return magnitude, phase

    def combine_fft(self,magnitude, phase):
        """Combine magnitude and phase into a single FFT."""
        combined = magnitude * np.exp(1j * phase)
        return np.fft.ifftshift(combined)

    def update_component(self, index, value):
        if self.selected_port == "Port 1":
            rect = self.freq_component_label[index].selection_rect
            if not rect:  # Handle case where no rectangle is selected
                return

            start_x, start_y, width, height = rect.x(), rect.y(), rect.width(), rect.height()
            value = value / 100  # Normalize slider value between 0 and 1

            x_end = min(start_x + width, self.image_magnitudes[index].shape[1])
            y_end = min(start_y + height, self.image_magnitudes[index].shape[0])

            if self.output_freq_components1 == "Magnitude":
                selected_magnitude = self.image_magnitudes[index][start_y:y_end, start_x:x_end].copy()
                selected_phase = self.image_phases[index][start_y:y_end, start_x:x_end].copy()

                # Scale the magnitude, but leave the phase unchanged
                self.weighted_magnitude[index] = selected_magnitude * value
                self.weighted_phase[index] = selected_phase
            else:
                selected_phase = self.image_phases[index][start_y:y_end, start_x:x_end].copy()
                selected_magnitude = self.image_magnitudes[index][start_y:y_end, start_x:x_end].copy()

                # Scale the phase, but leave the magnitude unchanged
                self.weighted_phase[index] = selected_phase * value
                self.weighted_magnitude[index] = selected_magnitude

            self.reconstruct_and_display_in_label(self.selected_port_indx)

    import numpy as np

    def mix_images(self, magnitude_list, phase_list, weights, modes):
        # Ensure lists are the same length
        # if len(magnitude_list) != len(phase_list) or len(magnitude_list) != len(weights):
        #     raise ValueError("Mismatch in lengths of magnitudes, phases, and weights.")

        # Initialize weighted magnitude and phase
        combined_magnitude = np.zeros_like(magnitude_list[0])
        combined_phase = np.zeros_like(phase_list[0])

        # Iterate through each image and mix based on weights and modes
        for i in range(len(weights)):
            weight = weights[i]
            mode = modes[i]

            if weight > 0:  # Only process if weight is non-zero
                if mode == "Magnitude":
                    # Add weighted magnitude
                    combined_magnitude += weight * magnitude_list[i]
                elif mode == "Phase":
                    # Add weighted phase
                    combined_phase += weight * phase_list[i]
                else:
                    raise ValueError(f"Invalid mode: {mode}. Use 'magnitude' or 'phase'.")

        # Normalize combined magnitude and phase
        total_weight = sum(weights)
        if total_weight > 0:
            combined_magnitude /= total_weight
            combined_phase /= total_weight

        # Reconstruct the mixed image using inverse FFT
        mixed_fft = combined_magnitude * np.exp(1j * combined_phase)
        mixed_image = np.abs(np.fft.ifft2(mixed_fft))

        return mixed_image

    def update_output(self):
        # Retrieve weights (slider values) and modes (comboBox selections)
        weights = [slider.value() / 100 for slider in self.sliders]  # Normalize slider values to [0, 1]
        modes = [comboBox.currentText() for comboBox in self.output_combo]

        # Mix images with the dynamically fetched weights and modes
        mixed_image = self.mix_images(self.image_magnitudes, self.image_phases, weights, modes)

        height, width = mixed_image.shape
        q_image = QImage(mixed_image.tobytes(), width, height, width, QImage.Format_Grayscale8)

        # Display in QLabel
        pixmap = QPixmap.fromImage(q_image)
        self.output_label[0].setPixmap(
            pixmap.scaled(self.output_label[0].size(), QtCore.Qt.KeepAspectRatio,
                          QtCore.Qt.SmoothTransformation))
        self.output_label[0].setAlignment(Qt.AlignCenter)



        # Display the mixed image
        self.display_image(mixed_image)

    def display_image(self, image):
        # Normalize the image
        normalized_image = self.normalize_image(image)

        # Convert numpy.ndarray to QImage
        height, width = normalized_image.shape
        # Ensure the image has the correct shape (grayscale image)
        q_image = QImage(normalized_image.data, width, height, width, QImage.Format_Grayscale8)

        # Convert QImage to QPixmap and set it to the QLabel
        pixmap = QPixmap.fromImage(q_image)
        self.output_label[0].setPixmap(pixmap)

    def normalize_image(self,image):
        # Normalize the image to range [0, 255]
        normalized = 255 * (image - np.min(image)) / (np.max(image) - np.min(image))
        return normalized.astype(np.uint8)

    def change_slider(self,index,value):
        self.update_output()


app = QtWidgets.QApplication([])
window = UI()
window.show()
app.exec_()
