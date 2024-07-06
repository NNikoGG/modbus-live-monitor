import sys
import time
import math
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QTableWidget, QTableWidgetItem, QScrollArea
from PyQt5.QtCore import QTimer, Qt
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusIOException

class ModbusMonitorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Modbus Live Monitor")
        self.setGeometry(100, 100, 1000, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        self.client = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_readings)
        self.tables = []
        self.update_interval = 1000  # Default update interval (1 second)

        self.setup_ui()

    def setup_ui(self):
        # Input fields
        input_layout = QHBoxLayout()
        self.layout.addLayout(input_layout)

        input_layout.addWidget(QLabel("IP:"))
        self.ip_input = QLineEdit("127.0.0.1")
        input_layout.addWidget(self.ip_input)

        input_layout.addWidget(QLabel("Port:"))
        self.port_input = QLineEdit("502")
        input_layout.addWidget(self.port_input)

        input_layout.addWidget(QLabel("Start Address:"))
        self.start_addr_input = QLineEdit("0")
        input_layout.addWidget(self.start_addr_input)

        input_layout.addWidget(QLabel("Number of Addresses:"))
        self.num_addr_input = QLineEdit("500")
        input_layout.addWidget(self.num_addr_input)

        # Buttons
        button_layout = QHBoxLayout()
        self.layout.addLayout(button_layout)

        self.start_button = QPushButton("Start Monitoring")
        self.start_button.clicked.connect(self.start_monitoring)
        button_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop Monitoring")
        self.stop_button.clicked.connect(self.stop_monitoring)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)

        # Update interval input and button
        interval_layout = QHBoxLayout()
        self.layout.addLayout(interval_layout)

        interval_layout.addWidget(QLabel("Update Interval (ms):"))
        self.interval_input = QLineEdit(str(self.update_interval))
        interval_layout.addWidget(self.interval_input)

        self.apply_interval_button = QPushButton("Apply Interval")
        self.apply_interval_button.clicked.connect(self.apply_update_interval)
        interval_layout.addWidget(self.apply_interval_button)

        # Scroll area for tables
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QHBoxLayout(self.scroll_content)
        self.scroll_area.setWidget(self.scroll_content)
        self.layout.addWidget(self.scroll_area)

        # Status label
        self.status_label = QLabel("Not connected")
        self.layout.addWidget(self.status_label)

    def create_table(self, rows):
        table = QTableWidget(rows, 2)
        table.setHorizontalHeaderLabels(["Address", "Value"])
        table.horizontalHeader().setStretchLastSection(True)
        table.verticalHeader().setVisible(False)
        table.setMinimumWidth(200)  # Set a minimum width for the table
        return table

    def start_monitoring(self):
        ip = self.ip_input.text()
        port = int(self.port_input.text())
        self.start_address = int(self.start_addr_input.text())
        self.num_addresses = int(self.num_addr_input.text())

        self.client = ModbusTcpClient(ip, port=port)
        if self.client.connect():
            self.status_label.setText(f"Connected to {ip}:{port}")
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.setup_tables()
            self.timer.start(self.update_interval)
        else:
            self.status_label.setText("Connection failed")

    def setup_tables(self):
        # Clear existing tables
        for table in self.tables:
            self.scroll_layout.removeWidget(table)
            table.deleteLater()
        self.tables.clear()

        # Create new tables
        addresses_per_table = 28
        num_tables = math.ceil(self.num_addresses / addresses_per_table)
        
        for i in range(num_tables):
            rows = min(addresses_per_table, self.num_addresses - i * addresses_per_table)
            table = self.create_table(rows)
            self.tables.append(table)
            self.scroll_layout.addWidget(table)

        # Set the width of the scroll content
        total_width = num_tables * 200  # Assuming each table is 200px wide
        self.scroll_content.setMinimumWidth(total_width)

    def stop_monitoring(self):
        if self.client:
            self.client.close()
        self.timer.stop()
        self.status_label.setText("Monitoring stopped")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def update_readings(self):
        if not self.client or not self.client.is_socket_open():
            self.stop_monitoring()
            return

        for table_index, table in enumerate(self.tables):
            start = self.start_address + table_index * 30
            end = min(start + 30, self.start_address + self.num_addresses)
            
            for i, address in enumerate(range(start, end)):
                try:
                    result = self.client.read_holding_registers(address=address, count=1, unit=1)
                    if not result.isError():
                        value = result.registers[0]
                    else:
                        value = "Error"
                except ModbusIOException:
                    value = "IO Error"
                except Exception:
                    value = "Unknown Error"

                table.setItem(i, 0, QTableWidgetItem(str(address)))
                table.setItem(i, 1, QTableWidgetItem(str(value)))

        self.status_label.setText(f"Last updated: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    def apply_update_interval(self):
        try:
            new_interval = int(self.interval_input.text())
            if new_interval < 100:  # Minimum interval of 100ms to prevent excessive updates
                raise ValueError("Interval too small")
            self.update_interval = new_interval
            if self.timer.isActive():
                self.timer.stop()
                self.timer.start(self.update_interval)
            self.status_label.setText(f"Update interval set to {self.update_interval}ms")
        except ValueError:
            self.status_label.setText("Invalid interval. Please enter a number >= 100")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ModbusMonitorGUI()
    window.show()
    sys.exit(app.exec_())