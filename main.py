from PyQt5 import uic
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog, QTableWidgetItem
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

    def create_list(self):
        try:
            self.creation = ListCreation()
            self.creation.exec()

        except Exception as x:
            print(x)

    def update_table(self):
        global CURRENT_ID
        current_row = 0
        con = sqlite3.connect(DB_NAME)
        cur = con.cursor()
        cur.execute(f'SELECT * from {LISTS_TABLE_NAME}')
        for elem in cur:
            name = str(elem[1])
            if self.tableWidget.rowCount() <= current_row:
                self.tableWidget.insertRow(current_row)
            self.tableWidget.setItem(current_row, 0, QTableWidgetItem(name))
            current_row += 1
        CURRENT_ID = max([elem[0] for elem in cur.execute(f'SELECT ID from {LISTS_TABLE_NAME}')]) + 1


class ListCreation(QDialog):
    def __init__(self):
        super().__init__()
        self.list_id = CURRENT_ID
        uic.loadUi("creation.ui", self)
        self.update_table()
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
                f'insert into {LISTS_TABLE_NAME} values ("{self.list_id}","{self.main_name}")')
            con.commit()
            self.closed = True
            self.close()

    def add_new_task(self, name, description, time, list_id):
        con = sqlite3.connect(DB_NAME)
        cur = con.cursor()
        cur.execute(
            f'insert into {TASKS_TABLE_NAME} values ("{str(name)}", "{str(description)}", "{str(time)}", "{list_id}")')
        con.commit()

    def update_table(self):
        current_row = 0
        con = sqlite3.connect(DB_NAME)
        cur = con.cursor()
        cur.execute(f'SELECT * from {TASKS_TABLE_NAME} WHERE list_id = {self.list_id}')
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
