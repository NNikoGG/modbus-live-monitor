import os
import sys
import time
import math
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QScrollArea,
    QComboBox,
    QMenuBar,
    QAction,
    QDialog,
    QTextEdit,
    QSpacerItem,
    QSizePolicy,
)
from PyQt5.QtCore import QTimer, Qt, QSize
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusIOException
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QFont


from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTextEdit,
    QPushButton,
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About Modbus Live Monitor")
        self.setFixedSize(450, 400)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        layout = QVBoxLayout()

        # Logos
        logo_layout = QHBoxLayout()

        logo_layout.addItem(
            QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
        )

        logo1 = QLabel()
        logo1_pixmap = QPixmap(logo1_path)
        logo1_pixmap = logo1_pixmap.scaled(
            100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        logo1.setPixmap(logo1_pixmap)
        logo_layout.addWidget(logo1)

        logo2 = QLabel()
        logo2_pixmap = QPixmap(logo2_path)
        logo2_pixmap = logo2_pixmap.scaled(
            80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        logo2.setPixmap(logo2_pixmap)
        logo_layout.addWidget(logo2)

        logo_layout.addItem(
            QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
        )

        layout.addLayout(logo_layout)

        # Title
        title_label = QLabel("Modbus Live Monitor")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title_label)

        # Version
        version_label = QLabel("Version 1.0")
        version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(version_label)

        # Credits
        credits = QTextEdit()
        credits.setReadOnly(True)
        credits.setHtml(
            """
            <div style="text-align: left;">
                <p><strong>Contributors:</strong> Nitish Gogoi, Kritanka Baruah, Jyotishman Patowary, Athikho Mao</p>
                <p><strong>Affiliation:</strong> Electronics and Telecommunications Engineering Department, Assam Engineering College</p>
                <p><strong>Developed for:</strong> Oil India Limited (OIL)</p>
                <p><strong>Project:</strong> This software is a collaborative effort between Assam Engineering College and Oil India Limited.</p>
            </div>
            """
        )
        layout.addWidget(credits)

        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

        self.setLayout(layout)


class ModbusMonitorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Modbus Live Monitor")
        self.setGeometry(100, 100, 1000, 600)
        self.setWindowIcon(create_icon())

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.client = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_readings)
        self.tables = []
        self.update_interval = 1000  # Default update interval (1 second)

        self.menubar = self.menuBar()
        help_menu = self.menubar.addMenu("Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

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
        self.num_addr_input = QLineEdit("100")
        input_layout.addWidget(self.num_addr_input)

        # Data type selection
        input_layout.addWidget(QLabel("Data Type:"))
        self.data_type_combo = QComboBox()
        self.data_type_combo.addItems(
            ["Coils", "Discrete Inputs", "Input Registers", "Holding Registers"]
        )
        input_layout.addWidget(self.data_type_combo)

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
        table.setMinimumWidth(200)
        return table

    def start_monitoring(self):
        ip = self.ip_input.text()
        port = int(self.port_input.text())
        self.start_address = int(self.start_addr_input.text())
        self.num_addresses = int(self.num_addr_input.text())
        self.data_type = self.data_type_combo.currentText()

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
        addresses_per_table = 27
        num_tables = math.ceil(self.num_addresses / addresses_per_table)

        for i in range(num_tables):
            rows = min(
                addresses_per_table, self.num_addresses - i * addresses_per_table
            )
            table = self.create_table(rows)
            self.tables.append(table)
            self.scroll_layout.addWidget(table)

        # Set the width of the scroll content
        total_width = num_tables * 200
        self.scroll_content.setMinimumWidth(total_width)

    def stop_monitoring(self):
        if self.client:
            self.client.close()
        self.timer.stop()
        self.status_label.setText("Monitoring stopped")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def get_display_address(self, address):
        if self.data_type == "Coils":
            return f"{address + 1:05d}"
        elif self.data_type == "Discrete Inputs":
            return address + 10001
        elif self.data_type == "Input Registers":
            return address + 30001
        else:  # Holding Registers
            return address + 40001

    def update_readings(self):
        if not self.client or not self.client.is_socket_open():
            self.stop_monitoring()
            return

        for table_index, table in enumerate(self.tables):
            start = self.start_address + table_index * 28
            end = min(start + 28, self.start_address + self.num_addresses)

            for i, address in enumerate(range(start, end)):
                try:
                    if self.data_type == "Coils":
                        result = self.client.read_coils(
                            address=address, count=1, unit=1
                        )
                        value = result.bits[0] if not result.isError() else "Error"
                    elif self.data_type == "Discrete Inputs":
                        result = self.client.read_discrete_inputs(
                            address=address, count=1, unit=1
                        )
                        value = result.bits[0] if not result.isError() else "Error"
                    elif self.data_type == "Input Registers":
                        result = self.client.read_input_registers(
                            address=address, count=1, unit=1
                        )
                        value = result.registers[0] if not result.isError() else "Error"
                    else:  # Holding Registers
                        result = self.client.read_holding_registers(
                            address=address, count=1, unit=1
                        )
                        value = result.registers[0] if not result.isError() else "Error"
                except ModbusIOException:
                    value = "IO Error"
                except Exception:
                    value = "Unknown Error"

                display_address = self.get_display_address(address)
                table.setItem(i, 0, QTableWidgetItem(str(display_address)))
                table.setItem(i, 1, QTableWidgetItem(str(value)))

        self.status_label.setText(f"Last updated: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    def apply_update_interval(self):
        try:
            new_interval = int(self.interval_input.text())
            if (
                new_interval < 100
            ):  # Minimum interval of 100ms to prevent excessive updates
                raise ValueError("Interval too small")
            self.update_interval = new_interval
            if self.timer.isActive():
                self.timer.stop()
                self.timer.start(self.update_interval)
            self.status_label.setText(
                f"Update interval set to {self.update_interval}ms"
            )
        except ValueError:
            self.status_label.setText("Invalid interval. Please enter a number >= 100")

    def show_about_dialog(self):
        about_dialog = AboutDialog(self)
        about_dialog.exec_()


def create_icon():
    pixmap = QPixmap(QSize(64, 64))
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    font = QFont()
    font.setPointSize(20)
    font.setBold(True)
    painter.setFont(font)
    painter.setPen(QColor(0, 0, 0))
    painter.drawText(pixmap.rect(), Qt.AlignCenter, "MLM")
    painter.end()
    return QIcon(pixmap)

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

logo1_path = resource_path('./resources/oil_logo.jpg')
logo2_path = resource_path('./resources/aec_logo.png')


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(create_icon())
    window = ModbusMonitorGUI()
    window.show()
    sys.exit(app.exec_())
