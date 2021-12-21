import json
import random
from datetime import date

import peewee
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QMessageBox

from globalUI import Ui_timetable
from meet import Ui_Meet
from models import *


def getClassNum(s):
    return int(s[:-1])


def getClassChar(s):
    char = ''
    if not s[len(s) - 1].isdigit():
        char = s[len(s) - 1]
    return char

def mySort(classes):
    rez = []
    for i in range(1, 12):
        tmp = list(filter(lambda x: getClassNum(x) == i, classes))
        tmp.sort()
        rez += tmp
    return rez

def gen(num):
    random.seed(num)
    a = ''
    b = ''
    for _ in range(6):
        a += str(random.random())[2]
        b += str(random.random())[2]
    passwd = int(a) ^ int(b)
    return passwd


class Connect(QtWidgets.QMainWindow):
    def __init__(self):
        super(Connect, self).__init__()
        self.ui = Ui_Meet()
        self.ui.setupUi(self)
        self.ui.lineEdit_2.setEchoMode(QtWidgets.QLineEdit.Password)
        self.ui.pushButton.pressed.connect(self.onPushButtonClicked)

    def onPushButtonClicked(self):
        isUser = False
        login = int(self.ui.lineEdit.text())
        passwd = int(self.ui.lineEdit_2.text())
        if self.ui.radioButton.isChecked():
            role = 1
            tmp = Teachers.select(Teachers.name).where(Teachers.id == login, Teachers.passwd == passwd)
        elif self.ui.radioButton_2.isChecked():
            role = 2
            tmp = Students.select(Students.fio.alias('name')).where(Students.id == login, Students.passwd == passwd)
        else:
            role = 0
            tmp = Admins.select(Admins.id.alias('name')).where(Admins.id == login, Admins.passwd == passwd)
        name = ''
        if len(tmp) == 1:
            isUser = True
            name = tmp[0].name
        if isUser:
            self.close()
            self.tableUI = MainWindow(role=role, name=str(name))
            self.tableUI.show()

        else:
            QMessageBox.warning(self, 'Ошибка', 'Введен неверный логин или пароль', QMessageBox.Ok)



class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, role=0, name=''):
        super(MainWindow, self).__init__()
        self.role = role
        if date.today().month < 9:
            self.teachYear = date.today().year - 1
        else:
            self.teachYear = date.today().year
        self.ui = Ui_timetable()
        self.ui.setupUi(self)
        self.setWindowTitle(name)


        # инициализируем окна
        self.updateClasses()
        self.updateTableWidget()
        self.updateListSubj()
        self.updateListTeach()
        self.updateListClasses()
        self.updateSubjClassInMark()
        self.updateClassesInMarks()
        self.ui.comboBox.addItems([' '] + [chr(i + ord('а')) for i in range(33)])
        self.ui.comboBox_2.addItems([str(i) for i in range(1, 12)])
        self.ui.comboBox_8.addItems([str(i) + ' лет' for i in range(6, 21)])
        self.tableMarks()
        # распределяем сигналы
        self.ui.week_days.currentIndexChanged.connect(self.updateTableWidget)
        self.ui.classes.currentIndexChanged.connect(self.updateTableWidget)
        self.ui.apply_timetable.pressed.connect(self.apply_timetable)
        self.ui.pushButton_10.pressed.connect(self.addTeachinSub)
        self.ui.pushButton_11.pressed.connect(self.delTeachinSub)
        self.ui.pushButton_3.pressed.connect(self.delSubj)
        self.ui.pushButton_12.pressed.connect(self.saveSubj)
        self.ui.pushButton.pressed.connect(self.createSubj)
        self.ui.listWidget.currentTextChanged.connect(self.updateSubj)
        self.ui.pushButton_14.pressed.connect(self.addSubjinTeach)
        self.ui.pushButton_15.pressed.connect(self.delSubjinTeach)
        self.ui.listWidget_2.currentTextChanged.connect(self.updateTeacher)
        self.ui.pushButton_2.pressed.connect(self.createTeacher)
        self.ui.pushButton_4.pressed.connect(self.delTeach)
        self.ui.pushButton_13.pressed.connect(self.saveTeacher)
        self.ui.listWidget_6.currentRowChanged.connect(self.listClassesChanged)
        self.ui.pushButton_20.pressed.connect(self.addChild)
        self.ui.pushButton_18.pressed.connect(self.delChild)
        self.ui.listWidget_5.currentTextChanged.connect(self.listChildrenChanged)
        self.ui.pushButton_16.pressed.connect(self.saveChild)
        self.ui.comboBox_2.currentTextChanged.connect(self.correctClass)
        self.ui.pushButton_5.pressed.connect(self.addClass)
        self.ui.pushButton_6.pressed.connect(self.delClass)
        self.ui.pushButton_17.pressed.connect(self.saveClass)
        self.ui.comboBox_10.currentIndexChanged.connect(self.updateClassesInMarks)
        self.ui.comboBox_9.currentIndexChanged.connect(self.tableMarks)
        self.ui.dateEdit.dateChanged.connect(self.tableMarks)
        self.ui.dateEdit_2.dateChanged.connect(self.tableMarks)
        self.ui.pushButton_8.pressed.connect(self.ShowHide)
        self.ui.pushButton_7.pressed.connect(self.saveMark)
        self.ui.importJSON.pressed.connect(self.download_db_json)
        self.ui.importCSV.pressed.connect(self.download_db_csv)



        # иициализируем то что осталось
        if self.ui.listWidget.count():
            self.ui.listWidget.setCurrentRow(0)
        if self. ui.listWidget_2.count():
            self.ui.listWidget_2.setCurrentRow(0)
        if self.ui.listWidget_6.count():
            self.ui.listWidget_6.setCurrentRow(0)
        if self.ui.comboBox_10.count():
            self.ui.comboBox_10.setCurrentIndex(0)

        # ограничиваем функцинал если нет доступа к нему
        if self.role != 1:
            self.ui.pushButton_7.setEnabled(False)
        if self.role == 2:
            self.ui.comboBox_9.setHidden(True)
            self.ui.comboBox_10.setHidden(True)
            self.ui.label_16.setHidden(True)

        if self.role != 0:
            # Окно расписания
            self.ui.apply_timetable.setEnabled(False)
            self.ui.importCSV.setEnabled(False)
            self.ui.importJSON.setEnabled(False)

            # Окно предметов
            self.ui.pushButton_10.hide()
            self.ui.pushButton_11.hide()
            self.ui.pushButton_12.hide()
            self.ui.pushButton.hide()
            self.ui.pushButton_3.hide()
            self.ui.comboBox_5.hide()
            self.ui.comboBox_6.setEnabled(False)
            self.ui.lineEdit_4.setReadOnly(True)
            self.ui.label_11.move(QtCore.QPoint(350, 20))
            self.ui.lineEdit_4.move(350, 50)
            self.ui.comboBox_4.setEnabled(False)
            mov = lambda name: name.move(QtCore.QPoint(name.x(), name.y() - 60))
            mov(self.ui.label_7)
            mov(self.ui.comboBox_4)
            mov(self.ui.comboBox_6)
            mov(self.ui.label_6)
            mov(self.ui.label_3)
            mov(self.ui.listWidget_3)
            self.ui.listWidget_3.setMinimumSize(331, 341)

            # Окно учителей
            self.ui.pushButton_2.hide()
            self.ui.pushButton_4.hide()
            self.ui.pushButton_13.hide()
            self.ui.pushButton_14.hide()
            self.ui.pushButton_15.hide()
            self.ui.comboBox_7.hide()
            self.ui.spinBox.setReadOnly(True)
            self.ui.lineEdit_5.setReadOnly(True)
            mov(self.ui.label_12)
            mov(self.ui.lineEdit_5)
            mov(self.ui.label_8)
            mov(self.ui.spinBox)
            mov(self.ui.label_4)
            mov(self.ui.listWidget_4)
            self.ui.listWidget_4.setMinimumSize(self.ui.listWidget_4.width(), self.ui.listWidget_4.height() + 210)

            # Окно классов
            self.ui.pushButton_5.hide()
            self.ui.pushButton_6.hide()
            self.ui.lineEdit.hide()
            self.ui.pushButton_20.hide()
            self.ui.pushButton_18.hide()
            self.ui.pushButton_16.hide()
            self.ui.pushButton_17.hide()
            self.ui.comboBox_2.setEnabled(False)
            self.ui.comboBox.setEnabled(False)
            self.ui.comboBox_8.setEnabled(False)
            self.ui.comboBox_3.setEnabled(False)

            mov(self.ui.label_14)
            mov(self.ui.label_15)
            mov(self.ui.comboBox)
            mov(self.ui.comboBox_2)
            mov(self.ui.groupBox)
            self.ui.groupBox.setMinimumSize(self.ui.groupBox.width(), self.ui.groupBox.height() + 120)
            self.ui.comboBox_8.move(self.ui.comboBox_8.x(), self.ui.comboBox_8.y() + 156)
            self.ui.comboBox_8.setMinimumSize(self.ui.comboBox_2.size())
            self.ui.comboBox_3.move(self.ui.comboBox_8.x() + self.ui.comboBox_8.width() + 9, self.ui.comboBox_8.y())
            self.ui.comboBox_3.setMinimumSize(self.ui.comboBox.size())
            self.ui.listWidget_5.setMinimumSize(self.ui.listWidget_5.width(), self.ui.listWidget_5.height() + 195)

            # скрываем окно администрации
            self.ui.tab_6.hide()
            self.ui.tabWidget.removeTab(5)
        else:
            self.adminList()
            self.ui.listWidget_7.currentRowChanged.connect(self.updateAdmin)
            self.ui.pushButton_22.pressed.connect(self.saveChange)
            self.ui.pushButton_21.pressed.connect(self.addAdmin)
            self.ui.pushButton_9.pressed.connect(self.deleteAdmin)



        # К О Н В Е Р Т И Р О В А Н И Е
        # pyuic5
        # globalUI.ui - o
        # globalUI.py
        # К О Н В Е Р Т И Р О В А Н И Е

    def write_json(self, filename, model_name):
        file = open(filename, "w")

        query = model_name.select().dicts()

        for i in query:
            json.dump(i, file, ensure_ascii=False, default=str)

        file.close()

    def download_db_csv(self):
        try:
            dbhandle.execute_sql('COPY (select * from students) TO \'D:/PythonDataBase/backup_data/csv/students.csv\''
                                 ' with (format csv, encoding \'win1251\', header true, delimiter \';\');')
            dbhandle.execute_sql('COPY (select * from classes) TO \'D:/PythonDataBase/backup_data/csv/classes.csv\''
                                 ' with (format csv, encoding \'win1251\', header true, delimiter \';\');')
            dbhandle.execute_sql('COPY (select * from classstudent) TO '
                                 '\'D:/PythonDataBase/backup_data/csv/classstudent.csv\''
                                 ' with (format csv, encoding \'win1251\', header true, delimiter \';\');')
            dbhandle.execute_sql('COPY (select * from classrooms) TO '
                                 '\'D:/PythonDataBase/backup_data/csv/classrooms.csv\''
                                 ' with (format csv, encoding \'win1251\', header true, delimiter \';\');')
            dbhandle.execute_sql('COPY (select * from teachers) TO \'D:/PythonDataBase/backup_data/csv/teachers.csv\''
                                 ' with (format csv, encoding \'win1251\', header true, delimiter \';\');')
            dbhandle.execute_sql('COPY (select * from subjects) TO \'D:/PythonDataBase/backup_data/csv/subjects.csv\''
                                 ' with (format csv, encoding \'win1251\', header true, delimiter \';\');')
            dbhandle.execute_sql('COPY (select * from subjectclass) TO '
                                 '\'D:/PythonDataBase/backup_data/csv/subjectclass.csv\''
                                 ' with (format csv, encoding \'win1251\', header true, delimiter \';\');')
            dbhandle.execute_sql('COPY (select * from teachersubject) TO \'D:/PythonDataBase/'
                                 'backup_data/csv/teachersubject.csv\''
                                 ' with (format csv, encoding \'win1251\', header true, delimiter \';\');')
            dbhandle.execute_sql('COPY (select * from timetable) TO \'D:/PythonDataBase/'
                                 'backup_data/csv/timetable.csv\''
                                 ' with (format csv, encoding \'win1251\', header true, delimiter \';\');')
            dbhandle.execute_sql('COPY (select * from lessons) TO \'D:/PythonDataBase/'
                                 'backup_data/csv/lessons.csv\''
                                 ' with (format csv, encoding \'win1251\', header true, delimiter \';\');')
            dbhandle.execute_sql('COPY (select * from marks) TO \'D:/PythonDataBase/'
                                 'backup_data/csv/marks.csv\''
                                 ' with (format csv, encoding \'win1251\', header true, delimiter \';\');')
        except:
            QtWidgets.QMessageBox.warning(self, 'Ошибка', 'При выгрузке данных произошла ошибка')


    def download_db_json(self):
        try:
            self.write_json("D:/PythonDataBase/backup_data/json/students.json", Students)
            self.write_json("D:/PythonDataBase/backup_data/json/classes.json", Classes)
            self.write_json("D:/PythonDataBase/backup_data/json/classstudent.json", ClassStudent)
            self.write_json("D:/PythonDataBase/backup_data/json/classrooms.json", Classrooms)
            self.write_json("D:/PythonDataBase/backup_data/json/teachers.json", Teachers)
            self.write_json("D:/PythonDataBase/backup_data/json/subjects.json", Subjects)
            self.write_json("D:/PythonDataBase/backup_data/json/subjectClass.json", SubjectClass)
            self.write_json("D:/PythonDataBase/backup_data/json/teachersubject.json", TeacherSubject)
            self.write_json("D:/PythonDataBase/backup_data/json/timetable.json", Timetable)
            self.write_json("D:/PythonDataBase/backup_data/json/lessons.json", Lessons)
            self.write_json("D:/PythonDataBase/backup_data/json/marks.json", Marks)
        except:
            QtWidgets.QMessageBox.warning(self, 'Ошибка', 'При выгрузке данных произошла ошибка')

    def deleteAdmin(self):
        id = self.ui.listWidget_7.item(self.ui.listWidget_7.currentRow()).text()
        adm = Admins.get(Admins.id == id)
        adm.delete_instance()
        self.adminList()

    def addAdmin(self):
        adm = Admins(
            passwd=0
        )
        adm.save()
        self.adminList()
        for i in range(self.ui.listWidget_7.count()):
            if self.ui.listWidget_7.item(i).text() == adm.id:
                self.ui.listWidget_7.setCurrentRow(i)

    def saveChange(self):
        id = self.ui.listWidget_7.item(self.ui.listWidget_7.currentRow()).text()
        tmp = Admins.get(Admins.id == id)
        adm = Admins(
            passwd=int(self.ui.lineEdit_6.text())
        )
        adm.save()
        tmp.delete_instance()
        self.adminList()

    def updateAdmin(self):
        if self.ui.listWidget_7.count() != 0:
            id = self.ui.listWidget_7.item(self.ui.listWidget_7.currentRow()).text()
            pas = Admins.get(Admins.id == id)
            self.ui.lineEdit_2.setText(str(pas.id))
            self.ui.lineEdit_6.setText(str(pas.passwd))
        else:
            self.ui.lineEdit_2.clear()
            self.ui.lineEdit_6.clear()

    def adminList(self):
        self.ui.listWidget_7.clear()
        admins = Admins.select(Admins.id)
        self.ui.listWidget_7.addItems([str(it.id) for it in admins])

    def tableMarksStudent(self):
        #     формируем список предметов
        st = Students.get(Students.fio == self.windowTitle())
        cls = (Classes.select(Classes.id, Classes.classnumber)
               .join(ClassStudent)
               .where(ClassStudent.studentID == st.id)
               .order_by(Classes.year.desc()))
        cls = cls[0]
        subjs = (Subjects.select(Subjects.name, Subjects.id)
                 .join(SubjectClass)
                 .where(SubjectClass.forclass == cls.classnumber))
        self.ui.tableWidget_2.clear()
        self.ui.tableWidget_2.setColumnCount(0)
        self.ui.tableWidget_2.setRowCount(len(subjs))
        self.ui.tableWidget_2.setVerticalHeaderLabels([s.name for s in subjs])
        #   собираем список оценок за текущий период
        marks = (Marks.select(Marks.markvalue, Subjects.name, Subjects.id, Lessons.date)
                 .join(Lessons)
                 .join(Timetable)
                 .join(TeacherSubject)
                 .join(Subjects)
                 .where(Marks.studentID == st.id,
                        Lessons.date.between(str(self.ui.dateEdit.date().toPyDate()),
                                             str(self.ui.dateEdit_2.date().toPyDate()))))

        values = {}
        for it in marks.objects():
            if str(values.get(it.date)) != 'None':
                if values[it.date].get(it.name):
                    values[it.date][it.name].append(it.markvalue)
                else:
                    values[it.date][it.name] = [it.markvalue]
            else:
                values[it.date] = dict([(it.name, [it.markvalue])])
        indexes = dict([(self.ui.tableWidget_2.verticalHeaderItem(i).text(), i) for i in range(0, self.ui.tableWidget_2.rowCount())])

        for dates in values.keys():
            self.ui.tableWidget_2.insertColumn(self.ui.tableWidget_2.columnCount())
            self.ui.tableWidget_2.setHorizontalHeaderItem(self.ui.tableWidget_2.columnCount() - 1,
                                                          QtWidgets.QTableWidgetItem(dates.strftime("%Y\n%m-%d")))
            for subj in values[dates].keys():
                if len(values[dates][subj]) != 0:
                    self.ui.tableWidget_2.setItem(indexes[subj], self.ui.tableWidget_2.columnCount()-1,
                                                  QtWidgets.QTableWidgetItem(str(values[dates][subj].pop(0))))

        # self.ui.tableWidget_2.insertColumn(self.ui.tableWidget_2.columnCount())
        # self.ui.tableWidget_2.setHorizontalHeaderItem(self.ui.tableWidget_2.columnCount() - 1,
        #                                               QtWidgets.QTableWidgetItem("Средний\nбалл"))
        # for i in range(self.ui.tableWidget_2.rowCount()):
        #     count = 0
        #     sum = 0
        #     for j in range(self.ui.tableWidget_2.columnCount()-1):
        #         if str(self.ui.tableWidget_2.item(i, j).text()) != 'None':
        #             count += 1
        #             sum += int(self.ui.tableWidget_2.item(i, j).text())
            # self.ui.tableWidget_2.setItem(i, self.ui.tableWidget_2.columnCount()-1,
            #                               QtWidgets.QTableWidgetItem(str((sum*1.0/count if count else ''))))

        self.ui.tableWidget_2.resizeColumnsToContents()



    def saveMark(self):
        values = {}
        for col in range(self.ui.tableWidget_2.columnCount()):
            dt = QtCore.QDate.fromString(self.ui.tableWidget_2.horizontalHeaderItem(col).text(), "yyyy\nMM-dd")
            for row in range(self.ui.tableWidget_2.rowCount()):
                if str(self.ui.tableWidget_2.item(row, col)) != 'None':
                    name = self.ui.tableWidget_2.verticalHeaderItem(row).text().replace('\n', ' ')
                    if values.get(dt.toPyDate()):
                        if values[dt.toPyDate()].get(name):
                            values[dt.toPyDate()][name].append(int(self.ui.tableWidget_2.item(row, col).text()))
                        else:
                            values[dt.toPyDate()][name] = [int(self.ui.tableWidget_2.item(row, col).text())]
                    else:
                        values[dt.toPyDate()] = dict([(name, [int(self.ui.tableWidget_2.item(row, col).text())])])
        sub = Subjects.get(Subjects.name == self.ui.comboBox_10.currentText())
        clas = (Classes.get(Classes.classnumber == getClassNum(self.ui.comboBox_9.currentText()),
                            Classes.classChar == getClassChar(self.ui.comboBox_9.currentText()),
                            Classes.year == self.teachYear))
        sts = (Students.select(Students.id, Students.fio)
               .join(ClassStudent)
               .where(ClassStudent.classID == clas.id))
        # ключ имя студента - значение его id
        bufst = {}
        for st in sts.objects():
            bufst[st.fio] = st.id
        teachsubj = []
        teach = Teachers.get(Teachers.name == self.windowTitle())
        teachsubj = (TeacherSubject.select(TeacherSubject.id)
                     .where(TeacherSubject.teacherID == teach.id,
                            TeacherSubject.subjectID == sub.id))
        col = 0
        dt = QtCore.QDate.fromString(self.ui.tableWidget_2.horizontalHeaderItem(col).text(), "yyyy\nMM-dd")
        weekdays = {dt.dayOfWeek()}
        flag = True
        while flag:
            col += 1
            dt = QtCore.QDate.fromString(self.ui.tableWidget_2.horizontalHeaderItem(col).text(), "yyyy\nMM-dd")
            if dt.dayOfWeek() in weekdays:
                if QtCore.QDate.fromString(self.ui.tableWidget_2.horizontalHeaderItem(col-1).text(), "yyyy\nMM-dd") == dt:
                    flag = True
                else:
                    flag = False
            else:
                weekdays.add(dt.dayOfWeek())
        timeteble = (Timetable.select(Timetable.id, Timetable.weekday)
                     .where(Timetable.classID == clas.id,
                            Timetable.year == self.ui.dateEdit.date().year(),
                            Timetable.weekday.in_(weekdays),
                            Timetable.teacherAndSubjID.in_(teachsubj)))
        for key in values.keys():
            lesson = (Lessons.select()
                      .where(Lessons.timetableID.in_([t.weekday for t in timeteble]),
                             Lessons.date == key))
            # словарь, где ключ - id ученика а значение список оценок
            cur_val = {}
            for k in values[key].keys():
                cur_val[bufst[k]] = values[key][k]
            for les in lesson.objects():
                marks = (Marks.select()
                         .where(Marks.lessonID == les.id))
                for mark in marks:
                    if cur_val.get(mark.studentID):
                        if mark.markvalue not in cur_val[mark.studentID]:
                            mark.delete_instance()
                            # for m in cur_val[mark.studentID]:
                            #     tmp = Marks(
                            #         studentID=mark.studentID,
                            #         markvalue=m,
                            #         lessonID=mark.lessonID
                            #     )
                            #     tmp.save()
                        else:
                            cur_val[mark.studentID].remove(mark.markvalue)
                            if len(cur_val[mark.studentID]) == 0:
                                cur_val.pop(mark.studentID)
                    else:
                        mark.delete_instance()

            # while len(cur_val) != 0:
            for timetable in timeteble:
                if timetable.weekday == key.weekday()+1:
                    les = Lessons(
                        timetableID=timetable.id,
                        date=key
                    )
                    les.save()

                    for i in cur_val.keys():
                        if len(cur_val[i]) == 0:
                            cur_val.pop(i)
                        else:
                            _mark = Marks(
                                studentID=i,
                                markvalue=cur_val[i].pop(0),
                                lessonID=les.id
                            )
                            _mark.save()


    def ShowHide(self):
        if self.ui.pushButton_8.text() == 'Скрыть пустые':
            self.ui.pushButton_8.setText('Показать пустые')
            for col in range(self.ui.tableWidget_2.columnCount()):
                emptRow = True
                row = 0
                while emptRow and row < self.ui.tableWidget_2.rowCount():
                    emptRow = True if str(self.ui.tableWidget_2.item(row, col)) == 'None' else False
                    row += 1
                if emptRow:
                    self.ui.tableWidget_2.hideColumn(col)
        else:
            self.ui.pushButton_8.setText('Скрыть пустые')
            for col in range(self.ui.tableWidget_2.columnCount()):
                self.ui.tableWidget_2.showColumn(col)

    def tableMarks(self):
        if self.role == 2:
            self.tableMarksStudent()
            return
        self.ui.tableWidget_2.clear()
        self.ui.tableWidget_2.setColumnCount(0)
        sub = Subjects.get(Subjects.name == self.ui.comboBox_10.currentText())
        clas = (Classes.get(Classes.classnumber == getClassNum(self.ui.comboBox_9.currentText()),
                            Classes.classChar == getClassChar(self.ui.comboBox_9.currentText()),
                            Classes.year == self.teachYear))
        strs = (Students.select(Students.fio)
                .join(ClassStudent)
                .where(ClassStudent.classID == clas.id))
        self.ui.tableWidget_2.setRowCount(len(strs))
        self.ui.tableWidget_2.setVerticalHeaderLabels(map(lambda a: a.replace(' ', '\n'), [it.fio for it in strs]))

        # Заполняем столбцы оценками и датами в выбранном промежутке
        # учитываем что может быть два и более предмета в день
        teachsubj = []
        if self.role == 0:
            teachsubj = (TeacherSubject.select(TeacherSubject.id)
                         .where(TeacherSubject.subjectID == sub.id))
        elif self.role == 1:
            teach = Teachers.get(Teachers.name == self.windowTitle())
            teachsubj = (TeacherSubject.select(TeacherSubject.id)
                         .where(TeacherSubject.teacherID == teach.id,
                                TeacherSubject.subjectID == sub.id))

        marks = (Marks.select(Marks.markvalue, Students.fio, Timetable.weekday, Lessons.date)
                 .join(Lessons)
                 .join(Timetable)
                 .join_from(Marks, Students)
                 .where(Timetable.classID == clas.id,
                        Lessons.date.between(str(self.ui.dateEdit.date().toPyDate()),
                                             str(self.ui.dateEdit_2.date().toPyDate())),
                        Timetable.teacherAndSubjID.in_(teachsubj))
                 .order_by(Timetable.lessonpos))
        correctDays = (Timetable.select(Timetable.weekday)
                       .where(Timetable.teacherAndSubjID.in_(teachsubj),
                              Timetable.classID == clas.id))
        correctDays = [it.weekday for it in correctDays]
        correctDays = dict([(day, correctDays.count(day)) for day in range(1, 8)])
        values = {}
        for it in marks.objects():
            if str(values.get(it.date)) != 'None':
                if values[it.date].get(it.fio.replace(' ', '\n')):
                    values[it.date][it.fio.replace(' ', '\n')].append(it.markvalue)
                else:
                    values[it.date][it.fio.replace(' ', '\n')] = [it.markvalue]
            else:
                values[it.date] = dict([(it.fio.replace(' ', '\n'), [it.markvalue])])

        dt = self.ui.dateEdit.date()
        while dt <= self.ui.dateEdit_2.date():
            if correctDays[dt.dayOfWeek()] != 0:
                correctDays[dt.dayOfWeek()] -= 1
                correctDays[7] += 1
                self.ui.tableWidget_2.insertColumn(self.ui.tableWidget_2.columnCount())
                self.ui.tableWidget_2.setHorizontalHeaderItem(self.ui.tableWidget_2.columnCount()-1,
                                                              QtWidgets.QTableWidgetItem(dt.toString("yyyy\nMM-dd")))
                # self.ui.tableWidget_2.setItemDelegateForRow(0, QtWidgets.QItemDelegate(QtWidgets.))
                if values.get(dt.toPyDate()):
                    for key in list(values[dt.toPyDate()].keys()):
                        row = 0
                        while self.ui.tableWidget_2.verticalHeaderItem(row).text() != key:
                            row += 1
                        self.ui.tableWidget_2.setItem(row, self.ui.tableWidget_2.columnCount()-1,
                                                      QtWidgets.QTableWidgetItem(str(values[dt.toPyDate()][key].pop(0))))
                        if len(values[dt.toPyDate()][key]) == 0:
                            values[dt.toPyDate()].pop(key)
                # else:
                #     for row in range(self.ui.tableWidget_2.rowCount()):
                #         self.ui.tableWidget_2.setItem(row, self.ui.tableWidget_2.columnCount()-1, QtWidgets.QTableWidgetItem(str()))

            else:
                correctDays[dt.dayOfWeek()] = correctDays[7]
                correctDays[7] = 0
                dt = dt.addDays(1)
        self.ui.tableWidget_2.resizeColumnsToContents()
        # self.ui.tableWidget_2.verticalHeaderItem(0).setToolTip('подсказка')


    def updateClassesInMarks(self):
        if self.role != 2:
            subj = self.ui.comboBox_10.currentText()
            classes = (SubjectClass.select(SubjectClass.forclass)
                       .join(Subjects)
                       .where(Subjects.name == subj)
                       .order_by(SubjectClass.forclass))
            fullclasses = (Classes.select(Classes.classnumber, Classes.classChar)
                           .where(Classes.classnumber.in_(classes)))
            ln = self.ui.comboBox_9.count()
            if ln > 1:
                self.ui.comboBox_9.setCurrentIndex(0)
            self.ui.comboBox_9.addItems(map(str, mySort([str(it.classnumber) + it.classChar for it in fullclasses])))
            for _ in range(ln-1):
                self.ui.comboBox_9.removeItem(1)
            if ln > 1:
                self.ui.comboBox_9.removeItem(0)

    def updateSubjClassInMark(self):
        if self.role == 1:
            teach = Teachers.get(Teachers.name == self.windowTitle()).id
            subj = (Subjects.select(Subjects.name)
                    .join(TeacherSubject)
                    .where(TeacherSubject.teacherID == teach))
            self.ui.comboBox_10.addItems([it.name for it in subj.objects()])
        elif self.role == 0:
            subj = (Subjects.select(Subjects.name))
            self.ui.comboBox_10.addItems([it.name for it in subj])

    def saveClass(self):
        name = self.ui.listWidget_6.currentItem()
        if name.text() == 'Новый класс':
            row = Classes(
                year=self.teachYear,
                classnumber=int(self.ui.comboBox_2.currentText()[:2:]),
                classChar=self.ui.comboBox.currentText()
            )
            row.save()
            QMessageBox.information(self, 'Успех', 'Новый класс добавлен', QMessageBox.Ok)
        else:
            row = Classes.get(Classes.classnumber == getClassNum(name.text()),
                              Classes.classChar == getClassChar(name.text()),
                              Classes.year == self.teachYear)
            row.classChar = self.ui.comboBox.currentText()
            row.classnumber = int(self.ui.comboBox_2.currentText()[:2:])
            row.save()
            QMessageBox.information(self, 'Успех', 'Данные о классе обновлены', QMessageBox.Ok)

        name.setText(str(row.classnumber) + row.classChar)
        tmp = [self.ui.listWidget_6.item(it).text() for it in range(self.ui.listWidget_6.count())]
        for i in range(self.ui.listWidget_6.count()-1):
            self.ui.listWidget_6.takeItem(0)
        self.ui.listWidget_6.addItems(mySort(tmp))
        self.ui.listWidget_6.takeItem(0)
        last_size = self.ui.classes.count()
        self.ui.classes.addItems(mySort(tmp))
        self.ui.classes.setCurrentIndex(self.ui.classes.count()-1)
        self.ui.comboBox_9.addItems(mySort(tmp))
        self.ui.comboBox_9.setCurrentIndex(self.ui.comboBox_9.count() - 1)
        for i in range(last_size):
            self.ui.classes.removeItem(0)
            self.ui.comboBox_9.removeItem(0)

    def delClass(self):
        ind = self.ui.listWidget_6.currentRow()
        if ind == -1:
            QMessageBox.warning(self, 'Ошибка', 'Выберите класс для удаления', QMessageBox.Ok)
            return
        if self.ui.listWidget_6.item(ind).text() == 'Новый класс':
            self.ui.listWidget_6.takeItem(ind)
        else:
            row = Classes.get(Classes.year == self.teachYear, Classes.classChar == self.ui.comboBox.currentText(),
                              Classes.classnumber == int(self.ui.comboBox_2.currentText()[:2:]))

            self.ui.listWidget_6.takeItem(ind)
            self.ui.classes.removeItem(self.ui.classes.findText(str(row.classnumber) + row.classChar))
            row.delete_instance()

    def addClass(self):
        for i in range(self.ui.listWidget_6.count()):
            if self.ui.listWidget_6.item(i).text() == 'Новый класс':
                QMessageBox.warning(self, 'Ошибка', 'Сначала отредактируйте добавленный класс', QMessageBox.Ok)
                return
        self.ui.listWidget_6.addItem('Новый класс')
        self.ui.listWidget_6.setCurrentRow(self.ui.listWidget_6.count() - 1)

    def correctClass(self):
        num = int(self.ui.comboBox_2.currentText())
        char = self.ui.comboBox.currentText()
        self.ui.comboBox.clear()
        classes = Classes.select(Classes.classChar).where(Classes.classnumber == num, Classes.year == self.teachYear)
        all = set([' '] + [chr(i + ord('а')) for i in range(33)])
        old = set([clas.classChar for clas in classes])
        tmp = all - old
        if self.ui.listWidget_6.currentItem().text() != 'Новый класс':
            tmp.add(char)
        tmp = list(tmp)
        tmp.sort()
        self.ui.comboBox.clear()
        self.ui.comboBox.addItems(tmp)
        self.ui.comboBox.setCurrentIndex(self.ui.comboBox.findText(char, QtCore.Qt.MatchExactly))

    def listChildrenChanged(self):
        ind = self.ui.listWidget_5.currentIndex().row()
        if ind >= 0:
            if self.ui.listWidget_5.item(ind).text() == 'Новый ученик':
                self.ui.lineEdit.setText('Новый ученик')
                self.ui.comboBox_8.setCurrentIndex(0)
                self.ui.comboBox_3.setCurrentIndex(0)
            else:
                curClass = Classes.get(Classes.classnumber == int(self.ui.comboBox_2.currentText()),
                                       Classes.classChar == self.ui.comboBox.currentText(),
                                       Classes.year == self.teachYear)
                child = Students.select().join(ClassStudent).where(Students.fio == self.ui.listWidget_5.item(ind).text(),
                                                                   ClassStudent.classID == curClass.id)
                child = child[0]
                self.ui.lineEdit.setText(child.fio)
                self.ui.comboBox_8.setCurrentIndex(child.age - 6)
                self.ui.comboBox_3.setCurrentIndex(not child.gender)

    def delChild(self):
        ind = self.ui.listWidget_5.currentRow()
        if ind == -1:
            QMessageBox.warning(self, 'Ошибка', 'Выберите ученика для удаления', QMessageBox.Ok)
            return
        text = self.ui.listWidget_5.takeItem(ind).text()
        if text == 'Новый ученик':
            self.ui.listWidget_5.takeItem(ind)
        else:
            curClass = Classes.get(Classes.classnumber == int(self.ui.comboBox_2.currentText()),
                                   Classes.classChar == self.ui.comboBox.currentText(),
                                   Classes.year == self.teachYear)
            row = Students.select().join(ClassStudent).where(ClassStudent.classID == curClass.id,
                                                             Students.fio == text)
            row = row[0]
            row.delete_instance()

    def addChild(self):
        childs = [self.ui.listWidget_5.item(ind).text() for ind in range(self.ui.listWidget_5.count())]
        if 'Новый ученик' in childs:
            QMessageBox.warning(self, 'Внимание', 'Сначала заполните данные для уже созданного ученика', QMessageBox.Ok)
        else:
            self.ui.listWidget_5.addItem('Новый ученик')
            self.ui.listWidget_5.setCurrentRow(self.ui.listWidget_5.count()-1)

    def saveChild(self):
        name = self.ui.lineEdit.text()
        if self.ui.listWidget_6.currentItem().text() == 'Новый класс':
            QMessageBox.warning(self, 'Ошибка', 'Сначала сохраните класс', QMessageBox.Ok)
            return
        if name == '' or name == 'Новый ученик':
            QMessageBox.warning(self, 'Ошибка', 'Введите ФИО', QMessageBox.Ok)
            return
        curClass = Classes.get(Classes.classnumber == int(self.ui.comboBox_2.currentText()),
                               Classes.classChar == self.ui.comboBox.currentText(),
                               Classes.year == self.teachYear)
        if self.ui.listWidget_5.currentItem().text() == 'Новый ученик':
            row = Students(
                fio=name,
                age=int(self.ui.comboBox_8.currentText()[:2:]),
                gender=self.ui.comboBox_3.currentIndex() == '0',
                passwd=0
            )
            row.save()
            row.passwd = gen(1000+row.id)
            row.save()
            row2 = ClassStudent(
                classID=curClass.id,
                studentID=row.id
            )
            row2.save()
            self.ui.listWidget_5.currentItem().setText(name)
            self.ui.listWidget_5.model().sort(0)
            QMessageBox.information(self, 'Ученик добавлен', f'Логин: {row.id}\n' + f'Пароль: {row.passwd}', QMessageBox.Ok)
        else:
            row = Students.select().join(ClassStudent).where(Students.fio == self.ui.listWidget_5.currentItem().text(),
                                                             ClassStudent.classID == curClass.id)
            row = row[0]
            row.fio = self.ui.lineEdit.text()
            row.age = int(self.ui.comboBox_8.currentText()[:2:])
            row.gender = self.ui.comboBox_3.currentIndex() == 0
            row.save()
            self.ui.listWidget_5.currentItem().setText(name)
            self.ui.listWidget_5.model().sort(0)
            QMessageBox.information(self, 'Успех', 'Информация успешно обновлена', QMessageBox.Ok)

    def listClassesChanged(self):
        self.ui.lineEdit.clear()
        self.ui.listWidget_5.clear()
        self.ui.comboBox.clear()
        row = self.ui.listWidget_6.currentRow()
        text = self.ui.listWidget_6.item(row).text()
        if text == 'Новый класс':
            self.ui.lineEdit.clear()
            self.ui.comboBox_8.setCurrentIndex(0)
            self.ui.comboBox_3.setCurrentIndex(0)
            self.ui.comboBox.clear()
            self.ui.comboBox.addItem('я')
            self.ui.comboBox.setCurrentIndex(0)
            self.ui.comboBox_2.setCurrentIndex(0)
            if self.ui.comboBox_2.currentIndex() == 0:
                self.correctClass()
        else:
            num = getClassNum(text)
            char = getClassChar(text)
            self.ui.comboBox.addItem(char)
            self.ui.comboBox.setCurrentText(char)
            self.correctClass()
            self.ui.comboBox_2.setCurrentText(str(num))
            curClass = Classes.get(Classes.classnumber == num, Classes.classChar == char, Classes.year == self.teachYear)
            childrens = (Students.select(Students.fio)
                         .join(ClassStudent)
                         .where(ClassStudent.classID == curClass.id)
                         .order_by(Students.fio))
            for child in childrens.objects():
                self.ui.listWidget_5.addItem(child.fio)
            if len(childrens):
                self.ui.listWidget_5.setCurrentRow(0)

    def updateListClasses(self):
        self.ui.listWidget_6.clear()
        classes = Classes.select().where(Classes.year == self.teachYear).order_by(Classes.classnumber, Classes.classChar)
        for clas in classes:
            self.ui.listWidget_6.addItem(str(clas.classnumber) + clas.classChar)

    def saveTeacher(self):
        old_name = self.ui.listWidget_2.item(self.ui.listWidget_2.currentRow()).text()
        new_name = self.ui.lineEdit_5.text()
        teach = Teachers.select(Teachers.name)
        names = []
        for item in teach:
            names.append(item.name)
        if new_name == 'Новый учитель':
            QMessageBox.warning(self, 'Внимание', 'Внесите имя учителя', QMessageBox.Ok)
        elif new_name != old_name and names.count(new_name) != 0:
            QMessageBox.warning(self, 'Ошибка',
                                'Учитель с таким именем уже есть',
                                QMessageBox.Ok)
        elif old_name == 'Новый учитель':
            row = Teachers(name=new_name, exp=self.ui.spinBox.value())
            row.passwd = gen(row.id)
            row.save()
            teach = Teachers.get(Teachers.name == new_name)

            for index in range(int(self.ui.listWidget_4.count())):
                subj = Subjects.get(Subjects.name == self.ui.listWidget_4.item(index).text())
                row1 = TeacherSubject(teacherID=teach.id, subjectID=subj.id)
                row1.save()
            self.updateTableWidget()
            self.ui.listWidget_2.item(self.ui.listWidget_2.currentRow()).setText(new_name)
            self.ui.listWidget_2.model().sort(0)
            cur = self.ui.listWidget.currentRow()
            self.ui.listWidget.setCurrentRow(self.ui.listWidget.count() - 1)
            self.ui.listWidget.setCurrentRow(cur)

            QMessageBox.information(self, 'Учитель добавлен', f'Логин: {row.id}\nПароль:{row.passwd}', QMessageBox.Ok)
        else:

            teach = Teachers.get(Teachers.name == old_name)
            if new_name != old_name:
                teach.name = new_name
            teach.exp = self.ui.spinBox.value()
            teach.save()


            oldSubjects = set()
            tmpSubjects = TeacherSubject.select(Subjects.id).join(Subjects).where(TeacherSubject.teacherID == teach.id)
            for subject in tmpSubjects.objects():
                oldSubjects.add(subject.id)

            newSubjects = set()
            for index in range(int(self.ui.listWidget_4.count())):
                subject = Subjects.get(Subjects.name == self.ui.listWidget_4.item(index).text())
                newSubjects.add(subject.id)

            deleteSubjects = oldSubjects - newSubjects
            addSubjects = newSubjects - oldSubjects

            for subject in deleteSubjects:
                row = TeacherSubject.get(TeacherSubject.teacherID == teach.id, TeacherSubject.subjectID == subject)
                row.delete_instance()
            for subject in addSubjects:
                row = TeacherSubject(teacherID=teach.id, subjectID=subject)
                row.save()
            self.updateTableWidget()
            self.ui.listWidget_2.item(self.ui.listWidget_2.currentRow()).setText(new_name)
            self.ui.listWidget_2.model().sort(0)
            cur = self.ui.listWidget.currentRow()
            self.ui.listWidget.setCurrentRow(self.ui.listWidget.count() - 1)
            self.ui.listWidget.setCurrentRow(cur)
            QMessageBox.information(self, 'Успех', 'Данные учителя обновлены', QMessageBox.Ok)

    def createTeacher(self):
        names = []
        for it in range(self.ui.listWidget_2.count()):
            names.append(self.ui.listWidget_2.item(it).text())
        if 'Новый учитель' in names:
            QMessageBox.warning(self, 'Ошибка', 'Сначала отредактируйте добавленного учителя', QMessageBox.Ok)
        else:
            self.ui.listWidget_2.addItem('Новый учитель')
            self.ui.listWidget_2.setCurrentRow(self.ui.listWidget_2.count() - 1)

    def updateTeacher(self):
        ind = self.ui.listWidget_2.currentIndex().row()
        name = self.ui.listWidget_2.item(ind).text()
        if name == 'Новый учитель':
            self.ui.lineEdit_5.setText('Новый учитель')
            self.ui.spinBox.setValue(0)
            self.ui.listWidget_4.clear()
            self.updateSubjinTeach()
        else:
            self.ui.listWidget_4.clear()
            self.ui.comboBox_7.clear()
            teach = Teachers.get(Teachers.name == name)
            self.ui.lineEdit_5.setText(name)

            self.ui.spinBox.setValue(teach.exp)

            tmp = (TeacherSubject
                   .select(Subjects.name)
                   .join(Subjects)
                   .where(TeacherSubject.teacherID == teach.id))
            curSubj = set()
            for subject in tmp.objects():
                curSubj.add(subject.name)
                self.ui.listWidget_4.addItem(subject.name)
            tmp = Subjects.select(Subjects.name)
            potenSubj = set()
            for subject in tmp:
                potenSubj.add(subject.name)
            potenSubj = potenSubj - curSubj
            for subject in potenSubj:
                self.ui.comboBox_7.addItem(subject)
            self.ui.listWidget_4.model().sort(0)
            self.ui.comboBox_7.model().sort(0)

    def delTeach(self):
        ind = self.ui.listWidget_2.currentIndex().row()
        if self.ui.listWidget_2.item(ind).text() == 'Новый учитель':
            self.ui.listWidget_2.takeItem(ind)
        elif ind >= 0:
            teach = self.ui.listWidget_2.takeItem(ind).text()
            row = Teachers.get(Teachers.name == teach)
            row.delete_instance()
            self.updateTableWidget()
            QMessageBox.information(self, 'Успех', 'Учитель удален успешно', QMessageBox.Ok)
        else:
            QMessageBox.warning(self, 'Ошибка', 'Выберите учителя для удаления.', QMessageBox.Ok)

    def delSubjinTeach(self):
        ind = self.ui.listWidget_4.currentIndex().row()
        if ind >= 0:
            teach = self.ui.listWidget_4.takeItem(ind)
            self.ui.comboBox_7.addItem(teach.text())
            self.ui.comboBox_7.model().sort(0)
        else:
            QMessageBox.warning(self, 'Ошибка', 'Выберите предмет для удаления.', QMessageBox.Ok)

    def addSubjinTeach(self):
        teach = self.ui.comboBox_7.currentText()
        ind = self.ui.comboBox_7.currentIndex()
        if ind >= 0:
            self.ui.comboBox_7.removeItem(ind)
            self.ui.listWidget_4.addItem(teach)
            self.ui.listWidget_4.model().sort(0)
        else:
            QMessageBox.warning(self, 'Ошибка', 'Предмет выбран некорректно.', QMessageBox.Ok)

    def updateListTeach(self):
        self.ui.listWidget_2.clear()
        teachers = Teachers.select(Teachers.name)
        for teacher in teachers:
            self.ui.listWidget_2.addItem(teacher.name)
        self.ui.listWidget_2.model().sort(0)

    def updateSubjinTeach(self):
        self.ui.comboBox_7.clear()
        subjects = Subjects.select(Subjects.name)
        for subject in subjects:
            self.ui.comboBox_7.addItem(subject.name)
        self.ui.comboBox_7.model().sort(0)

    def createSubj(self):
        names = []
        for it in range(self.ui.listWidget.count()):
            names.append(self.ui.listWidget.item(it).text())
        if 'Новый предмет' in names:
            QMessageBox.warning(self, 'Ошибка', 'Сначала отредактируйте добавленный предмет', QMessageBox.Ok)
        else:
            self.ui.listWidget.addItem('Новый предмет')
            self.ui.listWidget.setCurrentRow(self.ui.listWidget.count()-1)

    def updateSubj(self):
        ind = self.ui.listWidget.currentIndex().row()
        name = self.ui.listWidget.item(ind).text()
        if name == 'Новый предмет':
            self.ui.lineEdit_4.setText('Новый предмет')
            self.ui.comboBox_4.setCurrentIndex(0)
            self.ui.comboBox_6.setCurrentIndex(0)
            self.ui.listWidget_3.clear()
            self.updateTeacherinSub()
        else:
            self.ui.listWidget_3.clear()
            self.ui.comboBox_5.clear()
            subj = Subjects.get(Subjects.name == name)
            self.ui.lineEdit_4.setText(name)

            maxClass = SubjectClass.select(fn.MAX(SubjectClass.forclass).alias('max')).where(SubjectClass.subjectID == subj.id)[0]
            minClass = SubjectClass.select(fn.MIN(SubjectClass.forclass).alias('min')).where(SubjectClass.subjectID == subj.id)[0]

            self.ui.comboBox_4.setCurrentIndex(minClass.min-1)
            self.ui.comboBox_6.setCurrentIndex(maxClass.max-1)

            tmp = (TeacherSubject
                   .select(Teachers.name)
                   .join(Teachers)
                   .where(TeacherSubject.subjectID == subj.id))
            curTeach = set()
            for teach in tmp.objects():
                curTeach.add(teach.name)
                self.ui.listWidget_3.addItem(teach.name)
            tmp = Teachers.select(Teachers.name)
            potenTeach = set()
            for teach in tmp:
                potenTeach.add(teach.name)
            potenTeach = potenTeach - curTeach
            for teach in potenTeach:
                self.ui.comboBox_5.addItem(teach)
            self.ui.listWidget_3.model().sort(0)
            self.ui.comboBox_5.model().sort(0)

    def saveSubj(self):
        old_name = self.ui.listWidget.item(self.ui.listWidget.currentRow()).text()
        new_name = self.ui.lineEdit_4.text()
        subj = Subjects.select(Subjects.name)
        names = []
        for item in subj:
            names.append(item.name)
        if new_name == 'Новый предмет':
            QMessageBox.warning(self, 'Внимание', 'Название предмета недопустимо', QMessageBox.Ok)
        elif new_name != old_name and names.count(new_name) != 0:
            QMessageBox.warning(self, 'Ошибка',
                                'Предмет с таким названием уже есть.\nИзмените название, либо отредактируйте существующий предмет.',
                                QMessageBox.Ok)
        elif old_name == 'Новый предмет':
            classes = []
            for clas in range(int(self.ui.comboBox_4.currentText()), int(self.ui.comboBox_6.currentText()) + 1):
                classes.append(clas)
            if classes:
                row = Subjects(name=new_name)
                row.save()
                subj = Subjects.get(Subjects.name == new_name)
                for clas in classes:
                    row = SubjectClass(subjectID=subj.id, forclass=clas)
                    row.save()
                for index in range(int(self.ui.listWidget_3.count())):
                    teach = Teachers.get(Teachers.name == self.ui.listWidget_3.item(index).text())
                    row = TeacherSubject(teacherID=teach.id, subjectID=subj.id)
                    row.save()
                self.updateTableWidget()
                cur = self.ui.listWidget_2.currentRow()
                self.ui.listWidget_2.setCurrentRow(self.ui.listWidget_2.count()-1)
                self.ui.listWidget_2.setCurrentRow(cur)
                self.ui.listWidget.item(self.ui.listWidget.currentRow()).setText(new_name)
                self.ui.listWidget.model().sort(0)
                QMessageBox.information(self, 'Успех', 'Предмет добавлен', QMessageBox.Ok)
            else:
                QMessageBox.warning(self, 'Ошибка', 'Выбран некорректный диапазон классов', QMessageBox.Ok)
        else:
            newClasses = set()
            for index in range(int(self.ui.comboBox_4.currentText()), int(self.ui.comboBox_6.currentText()) + 1):
                newClasses.add(index)
            if newClasses:
                subj = Subjects.get(Subjects.name == old_name)
                if new_name != old_name:
                    subj.name = new_name
                    subj.save()
                oldClasses = set()
                tmpClass = SubjectClass.select(SubjectClass.forclass).where(SubjectClass.subjectID == subj.id)
                for item in tmpClass:
                    oldClasses.add(item.forclass)

                deleteClasses = oldClasses - newClasses
                addClasses = newClasses - oldClasses

                for clas in deleteClasses:
                    row = SubjectClass.get(SubjectClass.forclass == clas, SubjectClass.subjectID == subj.id)
                    row.delete_instance()

                for clas in addClasses:
                    row = SubjectClass(forclass=clas, subjectID=subj.id)
                    row.save()

                oldTeachers = set()
                tmpTeachers = TeacherSubject.select(Teachers.id).join(Teachers).where(TeacherSubject.subjectID == subj.id)
                for teacher in tmpTeachers.objects():
                    oldTeachers.add(teacher.id)

                newTeachers = set()
                for index in range(int(self.ui.listWidget_3.count())):
                    teacher = Teachers.get(Teachers.name == self.ui.listWidget_3.item(index).text())
                    newTeachers.add(teacher.id)

                deleteTeachers = oldTeachers - newTeachers
                addTeachers = newTeachers - oldTeachers

                for teacher in deleteTeachers:
                    row = TeacherSubject.get(TeacherSubject.teacherID == teacher, TeacherSubject.subjectID == subj.id)
                    row.delete_instance()
                for teacher in addTeachers:
                    row = TeacherSubject(teacherID=teacher, subjectID=subj.id)
                    row.save()
                self.updateTableWidget()
                cur = self.ui.listWidget_2.currentRow()
                self.ui.listWidget_2.setCurrentRow(self.ui.listWidget_2.count() - 1)
                self.ui.listWidget_2.setCurrentRow(cur)
                self.ui.listWidget.item(self.ui.listWidget.currentRow()).setText(new_name)
                self.ui.listWidget.model().sort(0)
                QMessageBox.information(self, 'Успех', 'Данные предмета обновлены', QMessageBox.Ok)
            else:
                QMessageBox.warning(self, 'Ошибка', 'Неправильный диапазон классов', QMessageBox.Ok)

    def delSubj(self):
        ind = self.ui.listWidget.currentIndex().row()
        if self.ui.listWidget.item(ind).text() == 'Новый предмет':
            self.ui.listWidget.takeItem(ind)
        elif ind >= 0:
            sub = self.ui.listWidget.takeItem(ind).text()
            row = Subjects.get(Subjects.name == sub)
            row.delete_instance()
            self.updateTableWidget()
        else:
            QMessageBox.warning(self, 'Ошибка', 'Выберите предмет для удаления.', QMessageBox.Ok)

    def delTeachinSub(self):
        ind = self.ui.listWidget_3.currentIndex().row()
        if ind >= 0:
            teach = self.ui.listWidget_3.takeItem(ind)
            self.ui.comboBox_5.addItem(teach.text())
            self.ui.comboBox_5.model().sort(0)
        else:
            QMessageBox.warning(self, 'Ошибка', 'Выберите учителя для удаления.', QMessageBox.Ok)

    def addTeachinSub(self):
        teach = self.ui.comboBox_5.currentText()
        ind = self.ui.comboBox_5.currentIndex()
        if ind >= 0:
            self.ui.comboBox_5.removeItem(ind)
            self.ui.listWidget_3.addItem(teach)
            self.ui.listWidget_3.model().sort(0)
        else:
            QMessageBox.warning(self, 'Ошибка', 'Учитель выбран некорректно.', QMessageBox.Ok)

    def updateListSubj(self):
        self.ui.listWidget.clear()
        sub = Subjects.select(Subjects.name)
        for item in sub:
            self.ui.listWidget.addItem(item.name)
        self.ui.listWidget.model().sort(0)

    def updateTeacherinSub(self):
        teach = Teachers.select(Teachers.name)
        self.ui.comboBox_5.clear()
        for name in teach:
            self.ui.comboBox_5.addItem(name.name)
        self.ui.comboBox_5.model().sort(0)

    def apply_timetable(self):
        clasNum = getClassNum(self.ui.classes.currentText())
        clasChar = getClassChar(self.ui.classes.currentText())
        curClass = Classes.get((Classes.classnumber == clasNum) & (Classes.classChar == clasChar)).id
        curDay = self.ui.week_days.currentIndex() + 1
        curYear = self.teachYear
        i = 0

        nonCorrRows = ''
        count = 0
        if self.role == 0:
            tableItemText = lambda row, col: self.ui.tableWidget.cellWidget(row, col).currentText()
        else:
            tableItemText = lambda row, col: self.ui.tableWidget.item(row, col).text()
        isEmpt = lambda row, col: tableItemText(row, col) == ''
        for j in range(8):
            if not ((isEmpt(j, 0) and isEmpt(j, 1) and isEmpt(j, 2)) or not (
                    isEmpt(j, 0) or isEmpt(j, 1) or isEmpt(j, 2))):
                nonCorrRows = nonCorrRows + ' ' + str(j + 1) + ','
                count += 1

        nonCorrRows = nonCorrRows[:-1]
        msg = ''
        if count == 1:
            msg = 'Строка' + nonCorrRows + ' заполнена некорректно.'
        elif count != 0:
            msg = 'Строки' + nonCorrRows + ' заполнены некорректно.'
        if count != 0:
            QMessageBox.warning(self, 'Ошибка введенных данных', msg, QMessageBox.Ok)
        else:
            while i < 8:
                prev = (Timetable
                        .select()
                        .where((Timetable.year == self.teachYear)
                               & (Timetable.lessonpos == i + 1)
                               & (Timetable.classID == curClass)
                               & (Timetable.weekday == curDay)))
                if not (isEmpt(i, 0) or isEmpt(i, 1) or isEmpt(i, 2)):
                    curClassroom = Classrooms.get(
                        Classrooms.name == tableItemText(i, 1)).id
                    curLespos = i + 1
                    teacher = Teachers.get(Teachers.name == tableItemText(i, 2)).id
                    subject = Subjects.get(Subjects.name == tableItemText(i, 0)).id
                    teachSubj = TeacherSubject.get((TeacherSubject.subjectID == subject)
                                                   & (TeacherSubject.teacherID == teacher)).id

                    if len(prev) != 0:
                        prev = prev[0]
                        prev.classroomID = curClassroom
                        prev.teacherAndSubjID = teachSubj
                        prev.save()
                    else:
                        row = Timetable(
                            classID=curClass,
                            classroomID=curClassroom,
                            teacherAndSubjID=teachSubj,
                            lessonpos=curLespos,
                            weekday=curDay,
                            year=curYear
                        )
                        row.save()
                elif isEmpt(i, 0) and isEmpt(i, 1) and isEmpt(i, 2) and len(prev) != 0:
                    prev = prev[0]
                    prev.delete_instance()
                i += 1
            QMessageBox.information(self, 'Успех', 'Расписание сохранено.')

    def updateClasses(self):
        self.ui.classes.clear()

        query = (Classes
                 .select(Classes.classnumber, Classes.classChar)
                 .where(Classes.year == self.teachYear)
                 .order_by(Classes.classnumber, Classes.classChar))
        print(self.teachYear)
        classes = []
        for item in query:
            print(str(item.classnumber) + str(item.classChar))
            classes.append(str(item.classnumber) + str(item.classChar))
        self.ui.classes.addItems(classes)


    def updateTeachers(self):
        rows = self.ui.tableWidget.selectedIndexes()
        clasNum = getClassNum(self.ui.classes.currentText())
        clasChar = getClassChar(self.ui.classes.currentText())
        curClass = Classes.get((Classes.classnumber == clasNum) & (Classes.classChar == clasChar)).id
        day = 1 + self.ui.week_days.currentIndex()
        for i in rows:
            row = i.row()
            if self.role == 0:
                self.ui.tableWidget.removeCellWidget(row, 2)
            combo = QtWidgets.QComboBox()
            subjTmp = Subjects.select(Subjects.id).where(Subjects.name == self.sender().currentText())
            if len(subjTmp) != 0:
                tmpquery = (Teachers
                            .select(Teachers.name)
                            .join(TeacherSubject)
                            .join(Timetable)
                            .where((Timetable.lessonpos == row + 1)
                                   & (Timetable.year == self.teachYear)
                                   & (Timetable.weekday == day)
                                   & (Timetable.classID != curClass)))
                subjTmp = subjTmp[0]
                query = (Teachers
                         .select(Teachers.name)
                         .join(TeacherSubject)
                         .where((TeacherSubject.subjectID == subjTmp.id)
                                & (Teachers.name.not_in(tmpquery))))
                for item in query:
                    combo.addItem(item.name)
            combo.addItem('')
            if self.role == 0:
                self.ui.tableWidget.setCellWidget(row, 2, combo)
            self.ui.tableWidget.resizeColumnsToContents()

    def updateTableWidget(self):

        self.ui.tableWidget.setColumnCount(3)
        self.ui.tableWidget.setRowCount(8)
        self.ui.tableWidget.setHorizontalHeaderLabels(('Предмет', 'Кабинет', 'Учитель'))
        i = 0
        day = 1 + self.ui.week_days.currentIndex()
        clasNum = getClassNum(self.ui.classes.currentText())
        clasChar = getClassChar(self.ui.classes.currentText())
        curClass = Classes.get((Classes.classnumber == clasNum) & (Classes.classChar == clasChar)).id
        while i < 8:
            j = 0
            current = (Subjects
                       .select(Subjects.name.alias('subj'), Teachers.name.alias('teach'), Classrooms.name.alias('clas'))
                       .join(TeacherSubject)
                       .join(Timetable)
                       .join_from(TeacherSubject, Teachers)
                       .join_from(Timetable, Classrooms)
                       .where((Timetable.year == self.teachYear)
                              & (Timetable.weekday == day)
                              & (Timetable.classID == curClass)
                              & (Timetable.lessonpos == i + 1)))
            if len(current) != 0:
                current = current.objects()
            while j < 3:
                combo = QtWidgets.QComboBox()
                combo.addItem('')
                if j == 0:
                    query = (Subjects
                             .select(Subjects.name)
                             .join(SubjectClass)
                             .where((SubjectClass.forclass == clasNum)))
                    for item in query:
                        combo.addItem(item.name)

                    if len(current) != 0:
                        combo.setCurrentText(current[0].subj)
                    else:
                        combo.setCurrentIndex(0)
                elif j == 1:
                    tmpquery = (Classrooms
                                .select(Classrooms.name)
                                .join(Timetable)
                                .where((Timetable.lessonpos == i + 1)
                                       & (Timetable.year == self.teachYear)
                                       & (Timetable.weekday == day)
                                       & (Timetable.classID != curClass)))
                    query = Classrooms.select(Classrooms.name).where(Classrooms.name.not_in(tmpquery))
                    for item in query:
                        combo.addItem(item.name)
                    if len(current) != 0:
                        combo.setCurrentText(current[0].clas)
                    else:
                        combo.setCurrentIndex(0)
                else:
                    if self.role != 0:
                        subj = Subjects.select(Subjects.id).where(
                            Subjects.name == self.ui.tableWidget.item(i, 0).text())
                    else:
                        subj = Subjects.select(Subjects.id).where(
                            Subjects.name == self.ui.tableWidget.cellWidget(i, 0).currentText())
                    if len(subj) != 0:
                        subj = subj[0]
                        tmpquery = (Teachers
                                    .select(Teachers.name)
                                    .join(TeacherSubject)
                                    .join(Timetable)
                                    .where((Timetable.lessonpos == i + 1)
                                           & (Timetable.year == self.teachYear)
                                           & (Timetable.weekday == day)
                                           & (Timetable.classID != curClass)))
                        query = (Teachers
                                 .select(Teachers.name)
                                 .join(TeacherSubject)
                                 .where((TeacherSubject.subjectID == subj.id)
                                        & (Teachers.name.not_in(tmpquery))))
                        for item in query:
                            combo.addItem(item.name)
                        if len(current) != 0:
                            combo.setCurrentText(current[0].teach)
                        else:
                            combo.setCurrentIndex(0)

                if self.role != 0:
                    tmp = QtWidgets.QTableWidgetItem(combo.currentText())
                    self.ui.tableWidget.setItem(i, j, tmp)
                    self.ui.tableWidget.item(i, j).setFlags(
                        QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled
                    )
                else:
                    self.ui.tableWidget.setCellWidget(i, j, combo)
                j += 1
            i += 1
        if self.role == 0:
            i = 0
            while i < 8:
                self.ui.tableWidget.cellWidget(i, 0).currentTextChanged.connect(self.updateTeachers)
                i += 1
        self.ui.tableWidget.resizeColumnsToContents()


if __name__ == '__main__':
    try:
        dbhandle.connect()
    except peewee.InternalError as px:
        print(str(px))

    # try:
    #     Admins.create_table()
    #     Students.create_table()
    #     Classes.create_table()
    #     ClassStudent.create_table()
    #     Classrooms.create_table()
    #     Teachers.create_table()
    #     Subjects.create_table()
    #     SubjectClass.create_table()
    #     TeacherSubject.create_table()
    #     Timetable.create_table()
    #     Lessons.create_table()
    #     Marks.create_table()
    # except peewee.InternalError as px:
    #     print(str(px))

    app = QtWidgets.QApplication([])
    # application = MainWindow()
    # application.show()

    application = Connect()
    application.show()


    app.exec()