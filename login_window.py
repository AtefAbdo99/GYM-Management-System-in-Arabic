import hashlib
import time
import random
import string
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton, QLabel, QMessageBox, QInputDialog
from PyQt5.QtCore import Qt
from Database_manager import DatabaseManager

class LoginWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager()
        self.init_ui()
        self.failed_attempts = 0
        self.lockout_time = 0

    def init_ui(self):
        self.setWindowTitle("تسجيل الدخول")
        self.setFixedSize(300, 200)
        layout = QVBoxLayout()

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("اسم المستخدم")
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("كلمة المرور")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)

        login_button = QPushButton("تسجيل الدخول")
        login_button.clicked.connect(self.login)
        layout.addWidget(login_button)

        forgot_password_button = QPushButton("نسيت كلمة المرور")
        forgot_password_button.clicked.connect(self.forgot_password)
        layout.addWidget(forgot_password_button)

        self.message_label = QLabel()
        self.message_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.message_label)

        self.setLayout(layout)

    def login(self):
        if time.time() < self.lockout_time:
            remaining_time = int(self.lockout_time - time.time())
            self.message_label.setText(f"الحساب مقفل. حاول مرة أخرى بعد {remaining_time} ثانية")
            return

        username = self.username_input.text()
        password = self.password_input.text()
        hashed_password = self.hash_password(password)

        user = self.db_manager.get_user(username)
        if user and user[2] == hashed_password:
            self.failed_attempts = 0
            self.accept()
        else:
            self.failed_attempts += 1
            if self.failed_attempts >= 3:
                self.lockout_time = time.time() + 300  # Lock for 5 minutes
                self.message_label.setText("تم قفل الحساب لمدة 5 دقائق")
            else:
                remaining_attempts = 3 - self.failed_attempts
                self.message_label.setText(f"فشل تسجيل الدخول. {remaining_attempts} محاولات متبقية")

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def forgot_password(self):
        username, ok = QInputDialog.getText(self, "استعادة كلمة المرور", "أدخل اسم المستخدم:")
        if ok and username:
            user = self.db_manager.get_user(username)
            if user:
                new_password = self.generate_temporary_password()
                hashed_new_password = self.hash_password(new_password)
                self.db_manager.execute_query("UPDATE users SET password = ? WHERE username = ?", 
                                              (hashed_new_password, username))
                QMessageBox.information(self, "استعادة كلمة المرور", 
                                        f"تم إرسال كلمة مرور مؤقتة إلى بريدك الإلكتروني: {new_password}")
            else:
                QMessageBox.warning(self, "خطأ", "اسم المستخدم غير موجود")

    def generate_temporary_password(self):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    login_window = LoginWindow()
    if login_window.exec_() == QDialog.Accepted:
        # You can proceed to the main window here
        pass
    sys.exit(app.exec_())
