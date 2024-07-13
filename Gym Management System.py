import sys
import os
import hashlib
import shutil
import random
import csv
from PyQt5.QtWidgets import (QMainWindow, QWidget, QSpinBox, QDoubleSpinBox, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
                             QLineEdit, QTreeWidget, QTreeWidgetItem, QTabWidget, QComboBox,
                             QDialog, QFormLayout, QMessageBox, QInputDialog, QFileDialog,
                             QCalendarWidget, QApplication)
from PyQt5.QtGui import QIcon, QFont, QPixmap, QColor, QBrush
from PyQt5.QtCore import Qt, QDateTime
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from Database_manager import DatabaseManager
from login_window import LoginWindow
import barcode
from barcode.writer import ImageWriter
import arabic_reshaper
from bidi.algorithm import get_display
from datetime import datetime, timedelta

# Ensure the necessary directory exists for storing barcode images
os.makedirs("barcodes", exist_ok=True)

class GymManagementSystem(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager()
        self.initialize_ui()

    def initialize_ui(self):
        self.setWindowTitle("X 1 GYM")
        self.setGeometry(100, 100, 1200, 800)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)

        self.create_members_tab()
        self.create_plans_tab()
        self.create_equipment_tab()
        self.create_reports_tab()
        self.create_settings_tab()

        self.create_toolbar()

        self.theme_toggle = QPushButton("تبديل المظهر")
        self.theme_toggle.clicked.connect(self.toggle_theme)
        self.layout.addWidget(self.theme_toggle)

        self.set_style("Light")

    def create_toolbar(self):
        toolbar = self.addToolBar("الأدوات")

        check_in_action = toolbar.addAction("تسجيل دخول")
        check_in_action.triggered.connect(self.check_in_member)

        check_out_action = toolbar.addAction("تسجيل خروج")
        check_out_action.triggered.connect(self.check_out_member)

        export_action = toolbar.addAction("تصدير البيانات")
        export_action.triggered.connect(self.export_data)

        import_action = toolbar.addAction("استيراد البيانات")
        import_action.triggered.connect(self.import_data)

    def create_members_tab(self):
        members_widget = QWidget()
        layout = QVBoxLayout(members_widget)

        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("بحث عن عضو")
        self.search_input.textChanged.connect(self.search_members)
        search_button = QPushButton("بحث")
        search_button.clicked.connect(self.search_members)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_button)
        layout.addLayout(search_layout)

        self.members_tree = QTreeWidget()
        self.members_tree.setHeaderLabels([
            "ID", "الاسم", "الباركود", "الخطة", "تاريخ البدء", "تاريخ الانتهاء", 
            "آخر زيارة", "عدد الزيارات", "رقم الهاتف", "البريد الإلكتروني", 
            "حالة الاشتراك", "الأيام المتبقية"
        ])
        self.members_tree.setColumnCount(12)

        # Set column widths
        column_widths = [50, 150, 100, 80, 100, 100, 100, 80, 100, 150, 100, 80]
        for i, width in enumerate(column_widths):
            self.members_tree.setColumnWidth(i, width)

        layout.addWidget(self.members_tree)

        buttons_layout = QHBoxLayout()
        buttons = [
            ("إضافة عضو", self.add_member_dialog),
            ("تعديل عضو", self.edit_member_dialog),
            ("حذف عضو", self.delete_member),
            ("تجديد الاشتراك", self.renew_subscription)
        ]
        for text, slot in buttons:
            button = QPushButton(text)
            button.clicked.connect(slot)
            buttons_layout.addWidget(button)
        layout.addLayout(buttons_layout)

        self.tab_widget.addTab(members_widget, "الأعضاء")
        self.load_members()

    def create_plans_tab(self):
        plans_widget = QWidget()
        layout = QVBoxLayout(plans_widget)

        self.plans_tree = QTreeWidget()
        self.plans_tree.setHeaderLabels(["ID", "اسم الخطة", "المدة (بالأيام)", "السعر"])
        layout.addWidget(self.plans_tree)

        buttons_layout = QHBoxLayout()
        add_button = QPushButton("إضافة خطة")
        add_button.clicked.connect(self.add_plan_dialog)
        edit_button = QPushButton("تعديل خطة")
        edit_button.clicked.connect(self.edit_plan_dialog)
        delete_button = QPushButton("حذف خطة")
        delete_button.clicked.connect(self.delete_plan)
        buttons_layout.addWidget(add_button)
        buttons_layout.addWidget(edit_button)
        buttons_layout.addWidget(delete_button)
        layout.addLayout(buttons_layout)

        self.tab_widget.addTab(plans_widget, "الخطط")
        self.load_plans()

    def add_plan_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("إضافة خطة جديدة")
        layout = QFormLayout(dialog)

        name_input = QLineEdit()
        duration_input = QSpinBox()
        duration_input.setMinimum(1)
        duration_input.setMaximum(365)
        price_input = QDoubleSpinBox()
        price_input.setMinimum(0)
        price_input.setMaximum(10000)

        layout.addRow("اسم الخطة:", name_input)
        layout.addRow("المدة (بالأيام):", duration_input)
        layout.addRow("السعر:", price_input)

        buttons = QHBoxLayout()
        save_button = QPushButton("حفظ")
        cancel_button = QPushButton("إلغاء")
        buttons.addWidget(save_button)
        buttons.addWidget(cancel_button)
        layout.addRow(buttons)

        save_button.clicked.connect(lambda: self.add_plan(name_input.text(), duration_input.value(), price_input.value(), dialog))
        cancel_button.clicked.connect(dialog.reject)

        dialog.exec_()

    def add_plan(self, name, duration, price, dialog):
        if not name:
            QMessageBox.warning(self, "خطأ", "يرجى إدخال اسم الخطة")
            return

        self.db_manager.add_plan(name, duration, price)
        self.load_plans()
        dialog.accept()
        QMessageBox.information(self, "نجاح", f"تمت إضافة الخطة {name} بنجاح")

    def edit_plan_dialog(self):
        selected_items = self.plans_tree.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "خطأ", "يرجى اختيار خطة لتعديلها")
            return

        plan_id = int(selected_items[0].text(0))
        plan = self.db_manager.fetch_one("SELECT * FROM plans WHERE id = ?", (plan_id,))

        dialog = QDialog(self)
        dialog.setWindowTitle("تعديل الخطة")
        layout = QFormLayout(dialog)

        name_input = QLineEdit(plan[1])
        duration_input = QSpinBox()
        duration_input.setMinimum(1)
        duration_input.setMaximum(365)
        duration_input.setValue(plan[2])
        price_input = QDoubleSpinBox()
        price_input.setMinimum(0)
        price_input.setMaximum(10000)
        price_input.setValue(plan[3])

        layout.addRow("اسم الخطة:", name_input)
        layout.addRow("المدة (بالأيام):", duration_input)
        layout.addRow("السعر:", price_input)

        buttons = QHBoxLayout()
        save_button = QPushButton("حفظ")
        cancel_button = QPushButton("إلغاء")
        buttons.addWidget(save_button)
        buttons.addWidget(cancel_button)
        layout.addRow(buttons)

        save_button.clicked.connect(lambda: self.update_plan(plan_id, name_input.text(), duration_input.value(), price_input.value(), dialog))
        cancel_button.clicked.connect(dialog.reject)

        dialog.exec_()

    def update_plan(self, plan_id, name, duration, price, dialog):
        if not name:
            QMessageBox.warning(self, "خطأ", "يرجى إدخال اسم الخطة")
            return

        self.db_manager.update_plan(plan_id, name, duration, price)
        self.load_plans()
        dialog.accept()
        QMessageBox.information(self, "نجاح", f"تم تحديث الخطة {name} بنجاح")

    def delete_plan(self):
        selected_items = self.plans_tree.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "خطأ", "يرجى اختيار خطة لحذفها")
            return

        plan_id = int(selected_items[0].text(0))
        plan_name = selected_items[0].text(1)

        reply = QMessageBox.question(self, "تأكيد الحذف",
                                     f"هل أنت متأكد من حذف الخطة {plan_name}؟",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.db_manager.delete_plan(plan_id)
            self.load_plans()
            QMessageBox.information(self, "نجاح", "تم حذف الخطة بنجاح")

    def load_plans(self):
        self.plans_tree.clear()
        plans = self.db_manager.fetch_all("SELECT * FROM plans")
        for plan in plans:
            item = QTreeWidgetItem(self.plans_tree)
            for i, value in enumerate(plan):
                item.setText(i, str(value))

    def create_equipment_tab(self):
        equipment_widget = QWidget()
        layout = QVBoxLayout(equipment_widget)

        self.equipment_tree = QTreeWidget()
        self.equipment_tree.setHeaderLabels(["ID", "اسم الجهاز", "الحالة", "تاريخ الصيانة الأخيرة"])
        layout.addWidget(self.equipment_tree)

        buttons_layout = QHBoxLayout()
        add_button = QPushButton("إضافة جهاز")
        add_button.clicked.connect(self.add_equipment_dialog)
        edit_button = QPushButton("تعديل جهاز")
        edit_button.clicked.connect(self.edit_equipment_dialog)
        delete_button = QPushButton("حذف جهاز")
        delete_button.clicked.connect(self.delete_equipment)
        maintenance_button = QPushButton("تسجيل صيانة")
        maintenance_button.clicked.connect(self.record_maintenance)
        buttons_layout.addWidget(add_button)
        buttons_layout.addWidget(edit_button)
        buttons_layout.addWidget(delete_button)
        buttons_layout.addWidget(maintenance_button)
        layout.addLayout(buttons_layout)

        self.tab_widget.addTab(equipment_widget, "الأجهزة")
        self.load_equipment()

    def load_equipment(self):
        self.equipment_tree.clear()
        equipment = self.db_manager.fetch_all("SELECT * FROM equipment")
        for item in equipment:
            tree_item = QTreeWidgetItem(self.equipment_tree)
            for i, value in enumerate(item):
                tree_item.setText(i, str(value))

    def add_equipment_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("إضافة جهاز جديد")
        layout = QFormLayout(dialog)

        name_input = QLineEdit()
        status_combo = QComboBox()
        status_combo.addItems(["صالح للاستخدام", "تحت الصيانة", "معطل"])

        layout.addRow("اسم الجهاز:", name_input)
        layout.addRow("الحالة:", status_combo)

        buttons = QHBoxLayout()
        save_button = QPushButton("حفظ")
        cancel_button = QPushButton("إلغاء")
        buttons.addWidget(save_button)
        buttons.addWidget(cancel_button)
        layout.addRow(buttons)

        save_button.clicked.connect(lambda: self.add_equipment(name_input.text(), status_combo.currentText(), dialog))
        cancel_button.clicked.connect(dialog.reject)

        dialog.exec_()

    def add_equipment(self, name, status, dialog):
        if not name:
            QMessageBox.warning(self, "خطأ", "يرجى إدخال اسم الجهاز")
            return

        self.db_manager.add_equipment(name, status)
        self.load_equipment()
        dialog.accept()
        QMessageBox.information(self, "نجاح", f"تمت إضافة الجهاز {name} بنجاح")

    def edit_equipment_dialog(self):
        selected_items = self.equipment_tree.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "خطأ", "يرجى اختيار جهاز لتعديله")
            return

        equipment_id = int(selected_items[0].text(0))
        equipment = self.db_manager.fetch_one("SELECT * FROM equipment WHERE id = ?", (equipment_id,))

        dialog = QDialog(self)
        dialog.setWindowTitle("تعديل الجهاز")
        layout = QFormLayout(dialog)

        name_input = QLineEdit(equipment[1])
        status_combo = QComboBox()
        status_combo.addItems(["صالح للاستخدام", "تحت الصيانة", "معطل"])
        status_combo.setCurrentText(equipment[2])

        layout.addRow("اسم الجهاز:", name_input)
        layout.addRow("الحالة:", status_combo)

        buttons = QHBoxLayout()
        save_button = QPushButton("حفظ")
        cancel_button = QPushButton("إلغاء")
        buttons.addWidget(save_button)
        buttons.addWidget(cancel_button)
        layout.addRow(buttons)

        save_button.clicked.connect(lambda: self.update_equipment(equipment_id, name_input.text(), status_combo.currentText(), dialog))
        cancel_button.clicked.connect(dialog.reject)

        dialog.exec_()

    def update_equipment(self, equipment_id, name, status, dialog):
        if not name:
            QMessageBox.warning(self, "خطأ", "يرجى إدخال اسم الجهاز")
            return

        self.db_manager.update_equipment(equipment_id, name, status)
        self.load_equipment()
        dialog.accept()
        QMessageBox.information(self, "نجاح", f"تم تحديث الجهاز {name} بنجاح")

    def delete_equipment(self):
        selected_items = self.equipment_tree.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "خطأ", "يرجى اختيار جهاز لحذفه")
            return

        equipment_id = int(selected_items[0].text(0))
        equipment_name = selected_items[0].text(1)

        reply = QMessageBox.question(self, "تأكيد الحذف",
                                     f"هل أنت متأكد من حذف الجهاز {equipment_name}؟",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.db_manager.delete_equipment(equipment_id)
            self.load_equipment()
            QMessageBox.information(self, "نجاح", "تم حذف الجهاز بنجاح")

    def record_maintenance(self):
        selected_items = self.equipment_tree.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "خطأ", "يرجى اختيار جهاز لتسجيل الصيانة")
            return

        equipment_id = int(selected_items[0].text(0))
        equipment_name = selected_items[0].text(1)

        self.db_manager.record_maintenance(equipment_id)
        self.load_equipment()
        QMessageBox.information(self, "نجاح", f"تم تسجيل صيانة الجهاز {equipment_name} بنجاح")

    def create_reports_tab(self):
        reports_widget = QWidget()
        layout = QVBoxLayout(reports_widget)

        report_types = ["تقرير الأعضاء النشطين", "تقرير الإيرادات", "تقرير الزيارات", "تقرير الأجهزة", "تقرير الاشتراكات المنتهية"]
        self.report_combo = QComboBox()
        self.report_combo.addItems(report_types)
        layout.addWidget(self.report_combo)

        generate_button = QPushButton("إنشاء التقرير")
        generate_button.clicked.connect(self.generate_report)
        layout.addWidget(generate_button)

        self.report_view = QWidget()
        report_layout = QVBoxLayout(self.report_view)
        layout.addWidget(self.report_view)

        self.tab_widget.addTab(reports_widget, "التقارير")

    def generate_report(self):
        report_type = self.report_combo.currentText()
        if report_type == "تقرير الأعضاء النشطين":
            self.active_members_report()
        elif report_type == "تقرير الإيرادات":
            self.revenue_report()
        elif report_type == "تقرير الزيارات":
            self.visits_report()
        elif report_type == "تقرير الأجهزة":
            self.equipment_report()
        elif report_type == "تقرير الاشتراكات المنتهية":
            self.expired_subscriptions_report()

    def active_members_report(self):
        active_count = self.db_manager.get_active_members_count()
        total_count = self.db_manager.get_total_members_count()
        inactive_count = total_count - active_count

        fig, ax = plt.subplots()
        ax.pie([active_count, inactive_count], 
            labels=[get_display(arabic_reshaper.reshape('نشط')), 
                    get_display(arabic_reshaper.reshape('غير نشط'))], 
            autopct='%1.1f%%')
        ax.set_title(get_display(arabic_reshaper.reshape('نسبة الأعضاء النشطين')))

        self.show_plot(fig)

    def revenue_report(self):
        data = self.db_manager.get_revenue_by_plan()

        plans = [row[0] for row in data]
        revenues = [row[2] for row in data]

        fig, ax = plt.subplots()
        ax.bar(plans, revenues)
        ax.set_xlabel(arabic_reshaper.reshape('الخطط'))
        ax.set_ylabel(arabic_reshaper.reshape('الإيرادات'))
        ax.set_title(arabic_reshaper.reshape('الإيرادات حسب الخطة'))

        self.show_plot(fig)

    def visits_report(self):
        data = self.db_manager.get_visits_last_30_days()

        dates = [row[0] for row in data]
        visits = [row[1] for row in data]

        fig, ax = plt.subplots()
        ax.plot(dates, visits)
        ax.set_xlabel('التاريخ')
        ax.set_ylabel('عدد الزيارات')
        ax.set_title('عدد الزيارات اليومية (آخر 30 يوم)')
        fig.autofmt_xdate()

        self.show_plot(fig)

    def equipment_report(self):
        equipment = self.db_manager.fetch_all("SELECT status, COUNT(*) FROM equipment GROUP BY status")

        statuses = [row[0] for row in equipment]
        counts = [row[1] for row in equipment]

        fig, ax = plt.subplots()
        ax.pie(counts, labels=statuses, autopct='%1.1f%%')
        ax.set_title('حالة الأجهزة')

        self.show_plot(fig)

    def expired_subscriptions_report(self):
        expired = self.db_manager.fetch_all(
            "SELECT COUNT(*) FROM members WHERE end_date < date('now')"
        )[0][0]
        active = self.db_manager.get_active_members_count()

        fig, ax = plt.subplots()
        ax.pie([active, expired], labels=['نشط', 'منتهي'], autopct='%1.1f%%')
        ax.set_title('نسبة الاشتراكات المنتهية')

        self.show_plot(fig)

    def show_plot(self, fig):
        try:
            for i in reversed(range(self.report_view.layout().count())):
                self.report_view.layout().itemAt(i).widget().setParent(None)

            # Fix Arabic text in the plot
            for ax in fig.get_axes():
                for text in ax.get_xticklabels() + ax.get_yticklabels():
                    text.set_text(get_display(arabic_reshaper.reshape(text.get_text())))
                ax.set_title(get_display(arabic_reshaper.reshape(ax.get_title())))
                if ax.get_legend():
                    for text in ax.get_legend().get_texts():
                        text.set_text(get_display(arabic_reshaper.reshape(text.get_text())))

            canvas = FigureCanvas(fig)
            self.report_view.layout().addWidget(canvas)
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء عرض التقرير: {str(e)}")
            print(f"Error in show_plot: {str(e)}")  # For debugging

    def export_data(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "تصدير البيانات", "", "CSV Files (*.csv)")
        if file_name:
            try:
                with open(file_name, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    # Export members
                    writer.writerow(['Members'])
                    writer.writerow(['ID', 'Name', 'Barcode', 'Plan', 'Start Date', 'End Date', 'Last Visit', 'Visits', 'Phone', 'Email'])
                    members = self.db_manager.fetch_all("SELECT * FROM members")
                    writer.writerows(members)

                    # Export plans
                    writer.writerow([])
                    writer.writerow(['Plans'])
                    writer.writerow(['ID', 'Name', 'Duration', 'Price'])
                    plans = self.db_manager.fetch_all("SELECT * FROM plans")
                    writer.writerows(plans)

                    # Export equipment
                    writer.writerow([])
                    writer.writerow(['Equipment'])
                    writer.writerow(['ID', 'Name', 'Status', 'Last Maintenance'])
                    equipment = self.db_manager.fetch_all("SELECT * FROM equipment")
                    writer.writerows(equipment)

                QMessageBox.information(self, "نجاح", "تم تصدير البيانات بنجاح")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء تصدير البيانات: {str(e)}")

    def import_data(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "استيراد البيانات", "", "CSV Files (*.csv)")
        if file_name:
            try:
                with open(file_name, 'r', newline='', encoding='utf-8') as file:
                    reader = csv.reader(file)
                    mode = None
                    for row in reader:
                        if 'Members' in row:
                            mode = 'members'
                            next(reader)  # Skip header
                        elif 'Plans' in row:
                            mode = 'plans'
                            next(reader)  # Skip header
                        elif 'Equipment' in row:
                            mode = 'equipment'
                            next(reader)  # Skip header
                        elif mode == 'members' and len(row) == 10:
                            self.db_manager.execute_query(
                                "INSERT OR REPLACE INTO members (id, name, barcode, plan, start_date, end_date, last_visit, visits, phone, email) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                tuple(row)
                            )
                        elif mode == 'plans' and len(row) == 4:
                            self.db_manager.execute_query(
                                "INSERT OR REPLACE INTO plans (id, name, duration, price) VALUES (?, ?, ?, ?)",
                                tuple(row)
                            )
                        elif mode == 'equipment' and len(row) == 4:
                            self.db_manager.execute_query(
                                "INSERT OR REPLACE INTO equipment (id, name, status, last_maintenance) VALUES (?, ?, ?, ?)",
                                tuple(row)
                            )
                self.load_members()
                self.load_plans()
                self.load_equipment()
                QMessageBox.information(self, "نجاح", "تم استيراد البيانات بنجاح")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء استيراد البيانات: {str(e)}")

    def backup_data(self):
        backup_dir = QFileDialog.getExistingDirectory(self, "اختر مجلد النسخ الاحتياطي")
        if backup_dir:
            try:
                backup_file = os.path.join(backup_dir, f"gym_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
                self.db_manager.execute_query("VACUUM INTO ?", (backup_file,))
                QMessageBox.information(self, "نجاح", f"تم إنشاء نسخة احتياطية بنجاح في:\n{backup_file}")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"فشل إنشاء النسخة الاحتياطية: {str(e)}")

    def restore_data(self):
        backup_file, _ = QFileDialog.getOpenFileName(self, "اختر ملف النسخة الاحتياطية", "", "SQLite DB Files (*.db)")
        if backup_file:
            reply = QMessageBox.warning(self, "تحذير",
                                        "سيؤدي استعادة النسخة الاحتياطية إلى استبدال جميع البيانات الحالية. هل أنت متأكد من المتابعة؟",
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                try:
                    self.db_manager.conn.close()
                    shutil.copy(backup_file, self.db_manager.db_name)
                    self.db_manager = DatabaseManager()  # Reinitialize the database connection
                    self.load_members()
                    self.load_plans()
                    self.load_equipment()
                    QMessageBox.information(self, "نجاح", "تمت استعادة البيانات بنجاح")
                except Exception as e:
                    QMessageBox.critical(self, "خطأ", f"فشل استعادة البيانات: {str(e)}")

    def change_password_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("تغيير كلمة المرور")
        layout = QFormLayout(dialog)

        current_password = QLineEdit()
        current_password.setEchoMode(QLineEdit.Password)
        new_password = QLineEdit()
        new_password.setEchoMode(QLineEdit.Password)
        confirm_password = QLineEdit()
        confirm_password.setEchoMode(QLineEdit.Password)

        layout.addRow("كلمة المرور الحالية:", current_password)
        layout.addRow("كلمة المرور الجديدة:", new_password)
        layout.addRow("تأكيد كلمة المرور الجديدة:", confirm_password)

        buttons = QHBoxLayout()
        save_button = QPushButton("حفظ")
        cancel_button = QPushButton("إلغاء")
        buttons.addWidget(save_button)
        buttons.addWidget(cancel_button)
        layout.addRow(buttons)

        save_button.clicked.connect(lambda: self.change_password(
            current_password.text(),
            new_password.text(),
            confirm_password.text(),
            dialog
        ))
        cancel_button.clicked.connect(dialog.reject)

        dialog.exec_()

    def change_password(self, current_password, new_password, confirm_password, dialog):
        if new_password != confirm_password:
            QMessageBox.warning(self, "خطأ", "كلمة المرور الجديدة وتأكيدها غير متطابقين")
            return

        hashed_current = hashlib.sha256(current_password.encode()).hexdigest()
        user = self.db_manager.fetch_one("SELECT * FROM users WHERE password = ?", (hashed_current,))

        if not user:
            QMessageBox.warning(self, "خطأ", "كلمة المرور الحالية غير صحيحة")
            return

        hashed_new = hashlib.sha256(new_password.encode()).hexdigest()
        self.db_manager.execute_query("UPDATE users SET password = ? WHERE id = ?", (hashed_new, user[0]))

        dialog.accept()
        QMessageBox.information(self, "نجاح", "تم تغيير كلمة المرور بنجاح")

    def toggle_theme(self):
        if self.palette().color(self.backgroundRole()).lightness() > 128:
            self.set_style("Dark")
        else:
            self.set_style("Light")

    def set_style(self, mode):
        if mode == "Dark":
            self.setStyleSheet("""
                QWidget {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QPushButton {
                    background-color: #4a4a4a;
                    border: 1px solid #646464;
                    padding: 5px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #646464;
                }
                QLineEdit, QComboBox {
                    background-color: #3a3a3a;
                    border: 1px solid #646464;
                    padding: 3px;
                    border-radius: 3px;
                }
                QTreeWidget {
                    background-color: #3a3a3a;
                    alternate-background-color: #454545;
                }
                QTreeWidget::item:selected {
                    background-color: #4a90d9;
                }
                QTabWidget::pane {
                    border: 1px solid #646464;
                }
                QTabBar::tab {
                    background-color: #3a3a3a;
                    border: 1px solid #646464;
                    padding: 5px;
                }
                QTabBar::tab:selected {
                    background-color: #4a4a4a;
                }
            """)
        else:
            self.setStyleSheet("""
                QWidget {
                    background-color: #f0f0f0;
                    color: #000000;
                }
                QPushButton {
                    background-color: #e0e0e0;
                    border: 1px solid #b0b0b0;
                    padding: 5px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #d0d0d0;
                }
                QLineEdit, QComboBox {
                    background-color: #ffffff;
                    border: 1px solid #b0b0b0;
                    padding: 3px;
                    border-radius: 3px;
                }
                QTreeWidget {
                    background-color: #ffffff;
                    alternate-background-color: #f5f5f5;
                }
                QTreeWidget::item:selected {
                    background-color: #308cc6;
                }
                QTabWidget::pane {
                    border: 1px solid #b0b0b0;
                }
                QTabBar::tab {
                    background-color: #e0e0e0;
                    border: 1px solid #b0b0b0;
                    padding: 5px;
                }
                QTabBar::tab:selected {
                    background-color: #f0f0f0;
                }
            """)

    def get_plan_names(self):
        plans = self.db_manager.fetch_all("SELECT name FROM plans")
        return [plan[0] for plan in plans]

    def create_settings_tab(self):
        settings_widget = QWidget()
        layout = QVBoxLayout(settings_widget)

        backup_button = QPushButton("نسخ احتياطي للبيانات")
        backup_button.clicked.connect(self.backup_data)
        layout.addWidget(backup_button)

        restore_button = QPushButton("استعادة البيانات")
        restore_button.clicked.connect(self.restore_data)
        layout.addWidget(restore_button)

        change_password_button = QPushButton("تغيير كلمة المرور")
        change_password_button.clicked.connect(self.change_password_dialog)
        layout.addWidget(change_password_button)

        self.tab_widget.addTab(settings_widget, "الإعدادات")


    def load_members(self):
        self.members_tree.clear()
        members = self.db_manager.fetch_all("SELECT * FROM members")
        for member in members:
            item = QTreeWidgetItem(self.members_tree)
            item.setText(0, str(member[0]))  # ID
            item.setText(1, member[1])       # Name
            item.setText(2, member[2])       # Barcode
            item.setText(3, member[3])       # Plan
            item.setText(4, member[4])       # Start Date
            item.setText(5, member[5])       # End Date
            item.setText(6, str(member[7]))  # Visits
            item.setText(7, member[8])       # Phone
            item.setText(8, member[9])       # Email
            status = self.check_subscription_status(member[5])
            item.setText(9, status)
            remaining_days = self.calculate_remaining_days(member[5])
            item.setText(10, str(remaining_days))
            
            barcode_number = member[2]
            if len(barcode_number) != 12:
                # If the barcode is not 12 digits, generate a new one
                barcode_number = self.generate_barcode()
                # Update the database with the new barcode
                self.db_manager.execute_query("UPDATE members SET barcode = ? WHERE id = ?", (barcode_number, member[0]))
            
            barcode_image_path = f"barcodes/{barcode_number}.png"
            self.generate_barcode_image(barcode_number, barcode_image_path)
            pixmap = QPixmap(barcode_image_path)
            barcode_label = QLabel()
            barcode_label.setPixmap(pixmap)
            item.setData(2, Qt.UserRole, barcode_label)

    
    def calculate_remaining_days(self, end_date):
        if not end_date:
            return "غير محدد"
        today = datetime.now().date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
        remaining = (end - today).days
        return max(0, remaining)

    def add_member_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("إضافة عضو جديد")
        layout = QFormLayout(dialog)

        name_input = QLineEdit()
        plan_combo = QComboBox()
        plan_combo.addItems(self.get_plan_names())
        phone_input = QLineEdit()
        email_input = QLineEdit()
        start_date = QCalendarWidget()
        start_date.setSelectedDate(QDateTime.currentDateTime().date())

        layout.addRow("الاسم:", name_input)
        layout.addRow("الخطة:", plan_combo)
        layout.addRow("رقم الهاتف:", phone_input)
        layout.addRow("البريد الإلكتروني:", email_input)
        layout.addRow("تاريخ البدء:", start_date)

        buttons = QHBoxLayout()
        save_button = QPushButton("حفظ")
        cancel_button = QPushButton("إلغاء")
        buttons.addWidget(save_button)
        buttons.addWidget(cancel_button)
        layout.addRow(buttons)

        save_button.clicked.connect(lambda: self.add_member(
            name_input.text(),
            plan_combo.currentText(),
            phone_input.text(),
            email_input.text(),
            start_date.selectedDate().toString(Qt.ISODate),
            dialog
        ))
        cancel_button.clicked.connect(dialog.reject)

        dialog.exec_()

    def add_member(self, name, plan, phone, email, start_date, dialog):
        if not name or not plan:
            QMessageBox.warning(self, "خطأ", "يرجى ملء الحقول الإلزامية")
            return

        end_date = self.calculate_end_date(plan, start_date)
        barcode = self.generate_barcode()

        self.db_manager.add_member(name, barcode, plan, start_date, end_date, phone, email)

        self.load_members()
        dialog.accept()
        QMessageBox.information(self, "نجاح", f"تمت إضافة العضو {name} بنجاح")

    def edit_member_dialog(self):
        selected_items = self.members_tree.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "خطأ", "يرجى اختيار عضو لتعديله")
            return

        member_id = int(selected_items[0].text(0))
        member = self.db_manager.fetch_one("SELECT * FROM members WHERE id = ?", (member_id,))

        dialog = QDialog(self)
        dialog.setWindowTitle("تعديل العضو")
        layout = QFormLayout(dialog)

        name_input = QLineEdit(member[1])
        plan_combo = QComboBox()
        plan_combo.addItems(self.get_plan_names())
        plan_combo.setCurrentText(member[3])
        phone_input = QLineEdit(member[8])
        email_input = QLineEdit(member[9])

        layout.addRow("الاسم:", name_input)
        layout.addRow("الخطة:", plan_combo)
        layout.addRow("رقم الهاتف:", phone_input)
        layout.addRow("البريد الإلكتروني:", email_input)

        buttons = QHBoxLayout()
        save_button = QPushButton("حفظ")
        cancel_button = QPushButton("إلغاء")
        buttons.addWidget(save_button)
        buttons.addWidget(cancel_button)
        layout.addRow(buttons)

        save_button.clicked.connect(lambda: self.update_member(
            member_id,
            name_input.text(),
            plan_combo.currentText(),
            phone_input.text(),
            email_input.text(),
            dialog
        ))
        cancel_button.clicked.connect(dialog.reject)

        dialog.exec_()

    def update_member(self, member_id, name, plan, phone, email, dialog):
        if not name or not plan:
            QMessageBox.warning(self, "خطأ", "يرجى ملء الحقول الإلزامية")
            return

        self.db_manager.update_member(member_id, name, plan, phone, email)

        self.load_members()
        dialog.accept()
        QMessageBox.information(self, "نجاح", f"تم تحديث بيانات العضو {name} بنجاح")

    def delete_member(self):
        selected_items = self.members_tree.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "خطأ", "يرجى اختيار عضو لحذفه")
            return

        member_id = int(selected_items[0].text(0))
        member_name = selected_items[0].text(1)

        reply = QMessageBox.question(self, "تأكيد الحذف",
                                     f"هل أنت متأكد من حذف العضو {member_name}؟",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.db_manager.delete_member(member_id)
            self.load_members()
            QMessageBox.information(self, "نجاح", "تم حذف العضو بنجاح")

    def renew_subscription(self):
        selected_items = self.members_tree.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "خطأ", "يرجى اختيار عضو لتجديد اشتراكه")
            return

        member_id = int(selected_items[0].text(0))
        member = self.db_manager.fetch_one("SELECT * FROM members WHERE id = ?", (member_id,))

        dialog = QDialog(self)
        dialog.setWindowTitle("تجديد الاشتراك")
        layout = QFormLayout(dialog)

        plan_combo = QComboBox()
        plan_combo.addItems(self.get_plan_names())
        plan_combo.setCurrentText(member[3])

        start_date = QCalendarWidget()
        start_date.setSelectedDate(QDateTime.currentDateTime().date())

        layout.addRow("الخطة:", plan_combo)
        layout.addRow("تاريخ البدء:", start_date)

        buttons = QHBoxLayout()
        save_button = QPushButton("تجديد")
        cancel_button = QPushButton("إلغاء")
        buttons.addWidget(save_button)
        buttons.addWidget(cancel_button)
        layout.addRow(buttons)

        save_button.clicked.connect(lambda: self.process_renewal(
            member_id,
            plan_combo.currentText(),
            start_date.selectedDate().toString(Qt.ISODate),
            dialog
        ))
        cancel_button.clicked.connect(dialog.reject)

        dialog.exec_()

    def process_renewal(self, member_id, plan, start_date, dialog):
        end_date = self.calculate_end_date(plan, start_date)

        self.db_manager.execute_query(
            "UPDATE members SET plan = ?, start_date = ?, end_date = ? WHERE id = ?",
            (plan, start_date, end_date, member_id)
        )

        self.load_members()
        dialog.accept()
        QMessageBox.information(self, "نجاح", "تم تجديد الاشتراك بنجاح")

    def calculate_end_date(self, plan, start_date):
        plan_duration = self.db_manager.fetch_one("SELECT duration FROM plans WHERE name = ?", (plan,))[0]
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = start + timedelta(days=plan_duration)
        return end.strftime("%Y-%m-%d")

    def generate_barcode(self):
        while True:
            barcode = ''.join([str(random.randint(0, 9)) for _ in range(12)])
            if not self.db_manager.fetch_one("SELECT * FROM members WHERE barcode = ?", (barcode,)):
                return barcode   

    def generate_barcode_image(self, barcode_number, barcode_path):
        try:
            ean = barcode.get('ean13', barcode_number, writer=ImageWriter())
            ean.save(barcode_path)
        except barcode.errors.BarcodeError as e:
            print(f"Error generating barcode: {e}")
            # You might want to generate a placeholder image or handle this error in some way

    def check_subscription_status(self, end_date):
        if not end_date:
            return "غير محدد"
        today = datetime.now().date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
        if end < today:
            return "منتهي"
        elif (end - today).days <= 7:
            return "على وشك الانتهاء"
        else:
            return "نشط"

    def search_members(self):
        search_term = self.search_input.text().lower()
        
        # If search term is empty, show all members
        if not search_term:
            self.load_members()
            return

        # Iterate through all items in the tree
        root = self.members_tree.invisibleRootItem()
        child_count = root.childCount()
        
        for i in range(child_count):
            item = root.child(i)
            match_found = False
            
            # Check if search term is in name, barcode, or phone
            for column in [1, 2, 7]:  # Adjust these indices if needed
                if search_term in item.text(column).lower():
                    match_found = True
                    self.highlight_item(item, search_term)
                    break
            
            # Show/hide the item based on match
            item.setHidden(not match_found)

    def highlight_item(self, item, search_term):
        highlight_color = QColor(255, 255, 0)  # Yellow highlight
        normal_color = QColor(255, 255, 255)  # White background
        
        for column in range(item.columnCount()):
            text = item.text(column).lower()
            if search_term in text:
                item.setBackground(column, QBrush(highlight_color))
            else:
                item.setBackground(column, QBrush(normal_color))

    def load_members(self):
        self.members_tree.clear()
        members = self.db_manager.fetch_all("SELECT * FROM members")
        for member in members:
            self.add_member_to_tree(member)
        

    def add_member_to_tree(self, member):
        item = QTreeWidgetItem(self.members_tree)
        
        # Assuming the order: ID, Name, Barcode, Plan, Start Date, End Date, Last Visit, Visits, Phone, Email
        for i in range(10):
            value = str(member[i]) if i < len(member) else ""
            item.setText(i, value)
        
        # Calculate and set subscription status
        status = self.check_subscription_status(member[5])  # Assuming End Date is at index 5
        item.setText(10, status)
        
        # Calculate and set remaining days
        remaining_days = self.calculate_remaining_days(member[5])
        item.setText(11, str(remaining_days))

    def check_in_member(self):
        barcode, ok = QInputDialog.getText(self, "تسجيل دخول", "أدخل الباركود:")
        if ok and barcode:
            self.process_check_in(barcode)

    def process_check_in(self, barcode):
        member = self.db_manager.fetch_one("SELECT * FROM members WHERE barcode = ?", (barcode,))
        if not member:
            QMessageBox.warning(self, "خطأ", "لم يتم العثور على عضو بهذا الباركود")
            return

        member_id, name = member[0], member[1]
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.db_manager.record_visit(member_id, current_date)
        self.db_manager.execute_query(
            "UPDATE members SET last_visit = ?, visits = visits + 1 WHERE id = ?",
            (current_date, member_id)
        )

        QMessageBox.information(self, "نجاح", f"تم تسجيل دخول {name} بنجاح")
        self.load_members()

    def check_out_member(self):
        barcode, ok = QInputDialog.getText(self, "تسجيل خروج", "أدخل الباركود:")
        if ok and barcode:
            self.process_check_out(barcode)

    def process_check_out(self, barcode):
        member = self.db_manager.fetch_one("SELECT * FROM members WHERE barcode = ?", (barcode,))
        if not member:
            QMessageBox.warning(self, "خطأ", "لم يتم العثور على عضو بهذا الباركود")
            return

        name = member[1]
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        QMessageBox.information(self, "نجاح", f"تم تسجيل خروج {name} بنجاح")

def main():
    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.RightToLeft)  # Set layout direction to Right-to-Left for Arabic

    db_manager = DatabaseManager()

    # Check if there's at least one user in the database
    if not db_manager.fetch_one("SELECT * FROM users"):
        # If no users exist, create an initial admin user
        initial_password = "admin123"  # You should change this immediately after first login
        hashed_password = hashlib.sha256(initial_password.encode()).hexdigest()
        db_manager.add_user("admin", hashed_password, "admin")
        print(f"Initial admin user created. Username: admin, Password: {initial_password}")

    # Assuming you have a LoginWindow class implemented
    login_window = LoginWindow()
    if login_window.exec_() == QDialog.Accepted:
        window = GymManagementSystem()
        window.show()
        sys.exit(app.exec_())

if __name__ == "__main__":
    main()

