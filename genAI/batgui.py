import sys
import serial
import random
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QProgressBar, QVBoxLayout, QWidget, QPushButton

class BatteryMonitor(QMainWindow):
    def __init__(self):
        super().__init__()

        # Initialize the UI and serial connection
        self.serial_port = None  # Initialize the serial port attribute to None initially
        self.battery_voltage = 3.7  # Default battery voltage (simulated)
        self.soc = 70  # Default state of charge (simulated)

        self.initUI()  # Setup the user interface

        self.init_serial_connection()  # Establish the serial connection

        # Create and configure a timer for periodic updates
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_battery_data)
        self.timer.start(1000)  # Update every second

    def initUI(self):
        """Initializes the User Interface (UI)."""
        # Set the main window properties
        self.setWindowTitle("Futuristic Battery Monitor")
        self.setGeometry(100, 100, 800, 600)

        # Apply the stylesheet for a futuristic look
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e2e;  /* Dark background */
                color: #ffffff;              /* White text */
            }

            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #00d4ff;             /* Neon blue text */
            }

            QPushButton {
                background-color: #2b2b40;  /* Dark button background */
                border: 2px solid #00d4ff;   /* Neon blue border */
                border-radius: 10px;         /* Rounded corners */
                color: #ffffff;              /* White text */
                font-size: 14px;
                padding: 10px;
            }

            QPushButton:hover {
                background-color: #00d4ff;  /* Neon blue on hover */
                color: #000000;             /* Black text on hover */
            }

            QProgressBar {
                border: 2px solid #00d4ff;  /* Blue border */
                border-radius: 5px;         /* Rounded corners */
                text-align: center;         /* Center text */
            }

            QProgressBar::chunk {
                background-color: #00d4ff;  /* Neon blue chunk */
                width: 20px;
            }
        """)

        # Create the central widget and layout
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout(self.central_widget)

        # Create labels to display battery data
        self.voltage_label = QLabel(self)
        self.voltage_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.voltage_label)

        self.soc_label = QLabel(self)
        self.soc_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.soc_label)

        # Create progress bar for SoC
        self.soc_bar = QProgressBar(self)
        self.soc_bar.setAlignment(Qt.AlignCenter)
        self.soc_bar.setRange(0, 100)
        layout.addWidget(self.soc_bar)

        # Create a button to simulate changes in battery status
        self.update_button = QPushButton("Simulate Battery Data", self)
        self.update_button.clicked.connect(self.simulate_battery_data)
        layout.addWidget(self.update_button)

        # Update the UI with the current battery data
        self.update_battery_data()

    def init_serial_connection(self):
        """Initializes the serial connection to the ESP32 (COM4)."""
        try:
            # Open the serial port (adjust COM port if necessary)
            self.serial_port = serial.Serial('COM4', 115200, timeout=1)
            print("Serial connection established on COM4.")
        except serial.SerialException as e:
            print(f"Error opening serial port: {e}")
            self.serial_port = None

    def read_from_serial(self):
        """Reads data from the ESP32 via serial port."""
        if self.serial_port and self.serial_port.in_waiting > 0:
            data = self.serial_port.readline().decode('utf-8').strip()
            return data
        return None

    def update_battery_data(self):
        """Updates battery data by reading from the serial or simulating."""
        data = self.read_from_serial()

        if data:
            try:
                # Assume data format is: "voltage,soc"
                voltage, soc = map(float, data.split(','))
                self.battery_voltage = voltage
                self.soc = int(soc)
            except ValueError:
                print("Invalid data received from ESP32.")
        else:
            # Fallback to simulated data if no serial data is available
            self.battery_voltage = random.uniform(3.0, 4.2)  # Simulate voltage between 3.0V and 4.2V
            self.soc = int((self.battery_voltage - 3.0) / (4.2 - 3.0) * 100)  # Calculate SoC based on voltage

        # Update the labels and progress bar
        self.voltage_label.setText(f"Voltage: {self.battery_voltage:.2f}V")
        self.soc_label.setText(f"State of Charge (SoC): {self.soc}%")
        self.soc_bar.setValue(self.soc)

    def simulate_battery_data(self):
        """Simulates a change in battery voltage."""
        self.battery_voltage = random.uniform(3.0, 4.2)  # Simulate a random voltage
        self.soc = int((self.battery_voltage - 3.0) / (4.2 - 3.0) * 100)  # Calculate the SoC
        self.update_battery_data()  # Update the display

def main():
    """Runs the application."""
    app = QApplication(sys.argv)
    ex = BatteryMonitor()  # Create the BatteryMonitor instance

    ex.show()  # Show the main window

    # Run the application event loop
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
