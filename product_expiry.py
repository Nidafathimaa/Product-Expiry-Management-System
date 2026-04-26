import sys
import sqlite3
from datetime import datetime, timedelta, date
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import QThread
from win10toast import ToastNotifier


# ================= DATABASE =================
def create_db():
    conn = sqlite3.connect("products.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS products(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            category TEXT,
            quantity INTEGER,
            expiry_date TEXT,
            remarks TEXT
        )
    """)
    conn.commit()
    conn.close()


# ================= NOTIFICATION THREAD =================
class WorkerThread(QThread):
    def run(self):
        try:
            conn = sqlite3.connect("products.db")
            c = conn.cursor()

            today = date.today()
            alert_date = today + timedelta(days=5)

            result = c.execute("SELECT name, expiry_date FROM products")
            data = result.fetchall()

            toaster = ToastNotifier()

            for name, exp in data:
                exp_date = datetime.strptime(exp, "%d-%m-%Y").date()

                if today <= exp_date <= alert_date:
                    toaster.show_toast(
                        "Expiry Alert",
                        f"{name} is expiring soon!",
                        duration=5
                    )

            conn.close()

        except Exception as e:
            print("Notification Error:", e)


# ================= ADD PRODUCT =================
class AddProduct(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Add Product")
        self.setFixedSize(300, 300)

        layout = QVBoxLayout()

        self.name = QLineEdit()
        self.name.setPlaceholderText("Product Name")

        self.category = QComboBox()
        self.category.addItems([
            "Beverage", "Cosmetics", "Medical",
            "Fruits", "Toiletries", "Chocolate"
        ])

        self.quantity = QSpinBox()

        self.expiry = QLineEdit()
        self.expiry.setPlaceholderText("DD-MM-YYYY")

        self.remarks = QLineEdit()
        self.remarks.setPlaceholderText("Remarks")

        btn = QPushButton("Add")
        btn.clicked.connect(self.add_data)

        layout.addWidget(self.name)
        layout.addWidget(self.category)
        layout.addWidget(self.quantity)
        layout.addWidget(self.expiry)
        layout.addWidget(self.remarks)
        layout.addWidget(btn)

        self.setLayout(layout)

    def add_data(self):
        conn = sqlite3.connect("products.db")
        c = conn.cursor()

        c.execute("""
            INSERT INTO products (name, category, quantity, expiry_date, remarks)
            VALUES (?, ?, ?, ?, ?)
        """, (
            self.name.text(),
            self.category.currentText(),
            self.quantity.value(),
            self.expiry.text(),
            self.remarks.text()
        ))

        conn.commit()
        conn.close()

        QMessageBox.information(self, "Success", "Product Added!")
        self.close()


# ================= SEARCH =================
class SearchProduct(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Search Product")
        self.setFixedSize(300, 150)

        layout = QVBoxLayout()

        self.input = QLineEdit()
        self.input.setPlaceholderText("Enter Product Name")

        btn = QPushButton("Search")
        btn.clicked.connect(self.search)

        layout.addWidget(self.input)
        layout.addWidget(btn)

        self.setLayout(layout)

    def search(self):
        conn = sqlite3.connect("products.db")
        c = conn.cursor()

        name = self.input.text()

        result = c.execute("SELECT * FROM products WHERE name=?", (name,))
        row = result.fetchone()

        if row:
            QMessageBox.information(self, "Result", str(row))
        else:
            QMessageBox.warning(self, "Error", "Not Found")

        conn.close()


# ================= DELETE =================
class DeleteProduct(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Delete Product")
        self.setFixedSize(300, 150)

        layout = QVBoxLayout()

        self.input = QLineEdit()
        self.input.setPlaceholderText("Enter Product ID")

        btn = QPushButton("Delete")
        btn.clicked.connect(self.delete)

        layout.addWidget(self.input)
        layout.addWidget(btn)

        self.setLayout(layout)

    def delete(self):
        conn = sqlite3.connect("products.db")
        c = conn.cursor()

        pid = self.input.text()

        c.execute("DELETE FROM products WHERE id=?", (pid,))
        conn.commit()
        conn.close()

        QMessageBox.information(self, "Deleted", "Product Deleted")
        self.close()


# ================= MAIN WINDOW =================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Product Expiry System")
        self.setGeometry(100, 100, 800, 500)

        self.table = QTableWidget()
        self.setCentralWidget(self.table)

        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID", "Name", "Category",
            "Quantity", "Expiry Date", "Remarks"
        ])

        toolbar = self.addToolBar("Toolbar")

        add_btn = QAction("Add", self)
        add_btn.triggered.connect(self.add)

        search_btn = QAction("Search", self)
        search_btn.triggered.connect(self.search)

        delete_btn = QAction("Delete", self)
        delete_btn.triggered.connect(self.delete)

        refresh_btn = QAction("Refresh", self)
        refresh_btn.triggered.connect(self.load_data)

        toolbar.addAction(add_btn)
        toolbar.addAction(search_btn)
        toolbar.addAction(delete_btn)
        toolbar.addAction(refresh_btn)

        self.load_data()

        # Start notification thread
        self.thread = WorkerThread()
        self.thread.start()

    def load_data(self):
        conn = sqlite3.connect("products.db")
        c = conn.cursor()

        result = c.execute("SELECT * FROM products")
        data = result.fetchall()

        self.table.setRowCount(0)

        for row_num, row_data in enumerate(data):
            self.table.insertRow(row_num)
            for col_num, data in enumerate(row_data):
                self.table.setItem(row_num, col_num, QTableWidgetItem(str(data)))

        conn.close()

    def add(self):
        dlg = AddProduct()
        dlg.exec_()
        self.load_data()

    def search(self):
        dlg = SearchProduct()
        dlg.exec_()

    def delete(self):
        dlg = DeleteProduct()
        dlg.exec_()
        self.load_data()


# ================= RUN APP =================
if __name__ == "__main__":
    create_db()

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())