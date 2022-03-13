from PyQt5 import uic, QtCore
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog, QTableWidgetItem, QMenu
import sys
import sqlite3

DB_NAME = "lists.db"
TASKS_TABLE_NAME = "tasks"
LISTS_TABLE_NAME = "lists"
CURRENT_ID = 0


class CheckList(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('main.ui', self)
        self.update_table()
        self.btn_create_list.clicked.connect(self.create_list)
        self.btn_update.clicked.connect(self.update_table)
        self.tableWidget.cellDoubleClicked.connect(self.edit_list)
        self.btn_start.clicked.connect(self.start_checking)
        self.tableWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tableWidget.customContextMenuRequested.connect(self.right_click_menu)

        self.tableWidget.viewport().installEventFilter(self)

    def create_list(self):
        global CURRENT_ID
        cur = sqlite3.connect(DB_NAME).cursor()
        CURRENT_ID = max([elem[0] for elem in cur.execute(f'SELECT ID from {LISTS_TABLE_NAME}')]) + 1
        self.creation = ListCreation()
        self.creation.exec()

    def edit_list(self, row):
        global CURRENT_ID
        row += 1
        CURRENT_ID = row
        self.creation = ListCreation()
        con = sqlite3.connect(DB_NAME)
        cur = con.cursor()
        elem = [*cur.execute(
            f'SELECT NAME from {LISTS_TABLE_NAME} where ID = {CURRENT_ID}')]
        self.creation.main_name.setPlainText(elem[0][0])
        self.creation.exec()

    def update_table(self):
        global CURRENT_ID
        current_row = 0
        self.tableWidget.setRowCount(1)
        con = sqlite3.connect(DB_NAME)
        cur = con.cursor()
        cur.execute(f'SELECT * from {LISTS_TABLE_NAME}')
        for elem in cur:
            name = str(elem[1])
            if self.tableWidget.rowCount() <= current_row:
                self.tableWidget.insertRow(current_row)
            self.tableWidget.setItem(current_row, 0, QTableWidgetItem(name))
            current_row += 1
        self.list_number.setMaximum(current_row)

    def eventFilter(self, source, event):
        if (event.type() == QtCore.QEvent.MouseButtonPress and
                event.buttons() == QtCore.Qt.RightButton and
                source is self.tableWidget.viewport()):
            item = self.tableWidget.itemAt(event.pos())
            if item is not None:
                self.menu = QMenu(self)
                self.start_checking_action = self.menu.addAction("Начать выполнение")
                self.menu.exec_(self.tableWidget.viewport().mapToGlobal(pos))
        return super(CheckList, self).eventFilter(source, event)

    def right_click_menu(self, position):
        self.menu.exec_(self.tableWidget.mapToGlobal(position))

    def start_checking(self):
        global CURRENT_ID
        CURRENT_ID = self.list_number.cleanText()


class ListCreation(QDialog):
    def __init__(self):
        super().__init__()
        self.list_id = CURRENT_ID
        uic.loadUi("creation.ui", self)
        self.update_table()
        self.btn_delete_list.clicked.connect(self.delete_list)
        self.btn_add_task.clicked.connect(self.save_task)
        self.btn_save_list.clicked.connect(self.save_list)
        self.btn_exit.clicked.connect(self.close)

    def save_task(self):
        if self.task_name.toPlainText() == "":
            self.task_warning_label.setText("Введите название задания")
        else:
            self.task_warning_label.setText("")
            if self.description.toPlainText() == "":
                self.task_warning_label.setText("Введите описание задания")
            else:
                self.task_warning_label.setText("")
                if self.task_time.time().hour() == 0 and self.task_time.time().minute() == 0:
                    self.task_warning_label.setText("Введите время на выполнение задания")
                else:
                    self.task_warning_label.setText("")
                    self.add_new_task(self.task_name.toPlainText(), self.description.toPlainText(),
                                      (self.task_time.time().hour(), self.task_time.time().minute()), self.list_id)
                    self.update_table()

    def save_list(self):
        if self.main_name.toPlainText() == "":
            self.task_warning_label.setText("Введите название чек-листа")
        else:
            con = sqlite3.connect(DB_NAME)
            cur = con.cursor()
            cur.execute(
                f'insert into {LISTS_TABLE_NAME} values ("{self.list_id}","{self.main_name.toPlainText()}")')
            con.commit()
            self.closed = True
            self.close()

    def add_new_task(self, name, description, time, list_id):
        con = sqlite3.connect(DB_NAME)
        cur = con.cursor()
        cur.execute(
            f'insert into {TASKS_TABLE_NAME} values ("{str(name)}", "{str(description)}", "{str(time)}", "{list_id}")')
        con.commit()

    def delete_list(self):
        con = sqlite3.connect(DB_NAME)
        cur = con.cursor()
        cur.execute(
            f'DELETE from {LISTS_TABLE_NAME} where ID = {CURRENT_ID}')
        cur.execute(f'DELETE from {TASKS_TABLE_NAME} where list_id = {CURRENT_ID}')
        con.commit()
        self.close()

    def update_table(self):
        current_row = 0
        con = sqlite3.connect(DB_NAME)
        cur = con.cursor()
        cur.execute(f'SELECT * from {TASKS_TABLE_NAME} WHERE list_id = {self.list_id}')
        self.tableWidget.setRowCount(1)
        for elem in cur:
            name = str(elem[0])
            description = str(elem[1])
            time = list(eval(elem[2]))
            if len(str(time[0])) == 1:
                time[0] = "0" + str(time[0])
            if len(str(time[1])) == 1:
                time[1] = "0" + str(time[1])
            time = f"{time[0]}:{time[1]}"
            if self.tableWidget.rowCount() <= current_row:
                self.tableWidget.insertRow(current_row)
            self.tableWidget.setItem(current_row, 0, QTableWidgetItem(name))
            self.tableWidget.setItem(current_row, 1, QTableWidgetItem(description))
            self.tableWidget.setItem(current_row, 2, QTableWidgetItem(time))
            current_row += 1


app = QApplication(sys.argv)
main = CheckList()
main.show()
sys.exit(app.exec())
