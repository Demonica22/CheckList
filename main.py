import datetime
import sqlite3
import sys

from PyQt5 import uic, QtCore, QtWidgets
from PyQt5.QtCore import QTimer, QTime, QDateTime
from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog, QTableWidgetItem

DB_NAME = "lists.db"
TASKS_TABLE_NAME = "tasks"
LISTS_TABLE_NAME = "lists"
USERS_TABLE_NAME = "users"


def time_in_secs(time):
    time = list(map(int, time.split(":")))
    time_in_seconds = 0
    for i in range(-len(time), 0, 1):
        time_in_seconds += time[i] * 60 ** abs(i + 1)
    return time_in_seconds


def time_parsing(time):  # return str from tuple  / (12,4) -> "12:04"
    time = list(eval(time))
    result = []
    for elem in time:
        if len(str(elem)) == 1:
            result.append("0" + str(elem))
        else:
            result.append(str(elem))
    return ":".join(result)


class CheckList(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('ui_forms/main.ui', self)
        self.update_table()
        self.current_id = 0
        self.btn_create_list.clicked.connect(self.create_list)
        self.btn_update.clicked.connect(self.update_table)
        self.lists_table.cellDoubleClicked.connect(self.edit_list)
        self.lists_table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.lists_table.customContextMenuRequested.connect(self.right_click_menu)

    def create_list(self):
        cur = sqlite3.connect(DB_NAME).cursor()
        self.current_id = max([elem[0] for elem in cur.execute(f'SELECT ID from {LISTS_TABLE_NAME}')]) + 1
        self.creation = ListCreation(self.current_id)
        self.creation.exec()

    def edit_list(self, row, column):
        text = self.lists_table.item(row, column).text().strip()
        con = sqlite3.connect(DB_NAME)
        cur = con.cursor()
        cur.execute(f'SELECT ID from {LISTS_TABLE_NAME} where name = ?', (text,))
        self.current_id = list(cur)[0][0]
        self.creation = ListCreation(self.current_id, editing=True)
        self.creation.main_name.setPlainText(text)
        self.creation.exec()

    def update_table(self):
        current_row = 0
        self.lists_table.setRowCount(1)
        con = sqlite3.connect(DB_NAME)
        cur = con.cursor()
        cur.execute(f'SELECT * from {LISTS_TABLE_NAME}')
        for elem in cur:
            name = str(elem[1])
            if self.lists_table.rowCount() <= current_row:
                self.lists_table.insertRow(current_row)
            self.lists_table.setItem(current_row, 0, QTableWidgetItem(name))
            current_row += 1
        cur.execute(f'SELECT * from {USERS_TABLE_NAME}')
        current_row = 0
        self.tasks_table.setRowCount(1)
        for elem in cur:
            if elem[3] == QDateTime.currentDateTime().toString("dd.MM.yyyy"):
                name = elem[1]
                lists_done = str(elem[2]).split(",")
                name_of_done_lists = []
                for elem in lists_done:
                    con = sqlite3.connect(DB_NAME)
                    cur = con.cursor()
                    cur.execute(f'SELECT name from {LISTS_TABLE_NAME} where ID=?', (elem,))
                    name_of_done_lists.append(*list(cur)[0])
                if self.tasks_table.rowCount() <= current_row:
                    self.tasks_table.insertRow(current_row)
                self.tasks_table.setItem(current_row, 0, QTableWidgetItem(name))
                self.tasks_table.setItem(current_row, 1, QTableWidgetItem(",".join(name_of_done_lists)))
                current_row += 1
        self.tasks_table.resizeColumnsToContents()

    def right_click_menu(self, position):
        item = self.lists_table.itemAt(position)
        if item is None:
            return
        con = sqlite3.connect(DB_NAME)
        cur = con.cursor()
        cur.execute(f'SELECT ID from {LISTS_TABLE_NAME} where name = ?', (item.text(),))
        self.current_id = list(cur)[0][0]
        cur.execute(f'SELECT * from {TASKS_TABLE_NAME} WHERE list_id = {self.current_id}')
        if len(list(cur)) != 0:
            menu = QtWidgets.QMenu()
            start_checking_action = menu.addAction("???????????? ????????????????????")
            action = menu.exec_(self.lists_table.viewport().mapToGlobal(position))
            if action == start_checking_action:
                self.start_checking()

    def start_checking(self):
        self.registration = RegistrationForm(list_id=self.current_id)
        self.registration.exec()


class ListCreation(QDialog):
    def __init__(self, current_id, editing=False):
        super().__init__()
        uic.loadUi("ui_forms/creation.ui", self)
        self.list_id = current_id
        self.editing = editing
        self.old_tasks = []
        self.new_tasks = []
        if self.editing:
            self.get_tasks_from_db()
        self.update_table()
        self.btn_delete_list.clicked.connect(self.delete_list)
        self.tasks_table.cellDoubleClicked.connect(self.remove_task)
        self.btn_add_task.clicked.connect(self.save_task)
        self.btn_save_list.clicked.connect(self.save_list)
        self.btn_exit.clicked.connect(self.close)

    def save_task(self):
        if self.task_name.toPlainText() == "":
            self.task_warning_label.setText("?????????????? ???????????????? ??????????????")
        else:
            self.task_warning_label.setText("")
            if self.description.toPlainText() == "":
                self.task_warning_label.setText("?????????????? ???????????????? ??????????????")
            else:
                self.task_warning_label.setText("")
                if self.task_time.time().minute() == 0 and self.task_time.time().second() == 0:
                    self.task_warning_label.setText("?????????????? ?????????? ???? ???????????????????? ??????????????")
                else:
                    self.task_warning_label.setText("")
                    self.add_new_task(self.task_name.toPlainText(), self.description.toPlainText(),
                                      (self.task_time.time().minute(), self.task_time.time().second()), self.list_id)
                    self.task_name.setText("")
                    self.description.setText("")
                    self.task_time.setTime(QTime(0, 0))
                    self.update_table()

    def remove_task(self, row, column):
        name = self.tasks_table.item(row, column).text().strip()
        for i in range(len(self.old_tasks)):
            if name in self.old_tasks[i]:
                list_id = self.old_tasks[i][3]
                con = sqlite3.connect(DB_NAME)
                cur = con.cursor()
                cur.execute(
                    f'DELETE from {TASKS_TABLE_NAME} where name = ? and list_id = ? ', (name, list_id,))
                con.commit()
                self.old_tasks.pop(i)
                return
        for i in range(len(self.new_tasks)):
            if name in self.new_tasks[i]:
                self.new_tasks.pop(i)
                return
        self.update_table()

    def save_list(self):
        if self.main_name.toPlainText() == "":
            self.task_warning_label.setText("?????????????? ???????????????? ??????-??????????")
        else:
            con = sqlite3.connect(DB_NAME)
            cur = con.cursor()
            # saving list
            if self.editing:
                cur.execute(f'UPDATE {LISTS_TABLE_NAME} SET name = ? where ID = ?',
                            (str(self.main_name.toPlainText().strip()), self.list_id))
            else:
                cur.execute(
                    f'insert into {LISTS_TABLE_NAME} values ("{self.list_id}","{self.main_name.toPlainText()}")')
            # saving all tasks
            for elem in self.new_tasks:
                cur.execute(
                    f'insert into {TASKS_TABLE_NAME} values ("{elem[0]}", "{elem[1]}", "{elem[2]}", "{elem[3]}")')

            con.commit()
            self.close()

    def add_new_task(self, name, description, time, list_id):
        self.new_tasks.append([str(name), str(description), (str(time)), list_id])

    def delete_list(self):
        con = sqlite3.connect(DB_NAME)
        cur = con.cursor()
        cur.execute(
            f'DELETE from {LISTS_TABLE_NAME} where ID = {self.list_id}')
        cur.execute(f'DELETE from {TASKS_TABLE_NAME} where list_id = {self.list_id}')
        con.commit()
        self.close()

    def get_tasks_from_db(self):
        con = sqlite3.connect(DB_NAME)
        cur = con.cursor()
        cur.execute(f'SELECT * from {TASKS_TABLE_NAME} WHERE list_id = {self.list_id}')
        self.old_tasks += list(cur)
        con.commit()

    def update_table(self):
        current_row = 0
        self.tasks_table.setRowCount(1)
        for elem in self.old_tasks + self.new_tasks:
            name = str(elem[0])
            description = str(elem[1])
            time = time_parsing(elem[2])
            if self.tasks_table.rowCount() <= current_row:
                self.tasks_table.insertRow(current_row)
            self.tasks_table.setItem(current_row, 0, QTableWidgetItem(name))
            self.tasks_table.setItem(current_row, 1, QTableWidgetItem(description))
            self.tasks_table.setItem(current_row, 2, QTableWidgetItem(time))
            current_row += 1


class RegistrationForm(QDialog):
    def __init__(self, list_id):
        super().__init__()
        uic.loadUi("ui_forms/registration.ui", self)
        self.list_id = list_id
        self.btn_start.clicked.connect(self.start)

    def start(self):
        if self.main_name.toPlainText() == "":
            self.warning_label.setText("?????????????? ??????")
        else:
            self.checker = Checker(user_name=self.main_name.toPlainText(), list_id=self.list_id)
            self.checker.exec()
            self.close()


class Checker(QDialog):
    def __init__(self, user_name, list_id):
        super().__init__()
        uic.loadUi("ui_forms/checking.ui", self)
        self.current_task = 0
        self.user_name = user_name
        self.list_id = list_id
        self.finished = False
        self.out_of_time = False
        self.timer = QTimer()
        self.timer.timeout.connect(self.show_time)
        self.timer.start(100)
        self.start()
        self.btn_continue.clicked.connect(self.load_task)

    def show_time(self):
        if self.finished:
            self.time_label.setText("")
        elif not self.out_of_time:
            current_timer_left = (self.current_task_duration - time_in_secs(
                QDateTime.currentDateTime().toString('mm:ss')) + self.task_start_time)
            if current_timer_left <= 0:
                self.out_of_time = True
                self.time_label.setText("???? ???? ???????????? ?????????????????? ?????????????? ??????????????!")
            else:
                if 0.5 < current_timer_left / self.current_task_duration <= 1:
                    self.time_label.setStyleSheet("color: rgb(0, 170, 0);")
                elif 0.25 < current_timer_left / self.current_task_duration <= 0.5:
                    self.time_label.setStyleSheet("color: rgb(218, 202, 64);")
                else:
                    self.time_label.setStyleSheet("color: rgb(255, 0, 0);")
                self.time_label.setText(str(datetime.timedelta(seconds=current_timer_left))[2:])

    def start(self):
        con = sqlite3.connect(DB_NAME)
        cur = con.cursor()
        cur.execute(f'SELECT * from {TASKS_TABLE_NAME} WHERE list_id = {self.list_id}')
        self.tasks = list(cur)
        self.load_task()

    def load_task(self):
        self.task_start_time = time_in_secs(QDateTime.currentDateTime().toString('mm:ss'))
        self.out_of_time = False
        self.progress_bar.setValue(int(self.current_task / len(self.tasks) * 100))
        if self.finished:
            self.load_statistics()
            self.close()
        elif self.current_task < len(self.tasks):
            task = self.tasks[self.current_task]
            self.task_name_label.setText(task[0])
            self.task_description_label.setText(task[1])
            self.current_task += 1
            self.current_task_duration = time_in_secs(time_parsing(task[2]))
        else:
            self.label.setText("")
            self.label_2.setText("")
            self.label_3.setText("")
            self.task_name_label.setText("")
            self.task_description_label.setStyleSheet("color: rgb(0, 170, 0);")
            self.time_label.setText("")
            self.task_description_label.setText("???? ?????????????????? ????????????????????.\n?????????????? ???????????????????? ?????? ????????????\n?? ????????")
            self.finished = True

    def load_statistics(self):
        con = sqlite3.connect(DB_NAME)
        cur = con.cursor()
        cur.execute(f'SELECT * from {USERS_TABLE_NAME} WHERE user_name = ?', (self.user_name,))
        users = [elem for elem in cur]
        if users != []:
            user_id = users[0][0]
            if users[0][3] == QDateTime.currentDateTime().toString("dd.MM.yyyy"):
                user_lists_done = str(users[0][2]).split(",") + [str(self.list_id)]
            else:
                user_lists_done = [str(self.list_id)]
            cur.execute(f'UPDATE {USERS_TABLE_NAME} SET lists_done = ?, date=? where ID = ?',
                        (",".join(user_lists_done), QDateTime.currentDateTime().toString("dd.MM.yyyy"), user_id,))
        else:
            cur.execute(f'insert into {USERS_TABLE_NAME}(user_name,lists_done,date) values (?,?,?)',
                        (self.user_name, str(self.list_id), QDateTime.currentDateTime().toString("dd.MM.yyyy"),))
        con.commit()


app = QApplication(sys.argv)
main = CheckList()
main.show()
sys.exit(app.exec())
