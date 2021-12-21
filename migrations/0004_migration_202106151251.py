# auto-generated snapshot
from peewee import *
import datetime
import peewee


snapshot = Snapshot()


@snapshot.append
class Admins(peewee.Model):
    passwd = IntegerField()
    class Meta:
        table_name = "admins"


@snapshot.append
class Classes(peewee.Model):
    year = IntegerField(constraints=[SQL('CHECK (year >= 1980)')])
    classChar = CharField(default='', max_length=1)
    classnumber = IntegerField(constraints=[SQL('CHECK (classnumber >= 1 AND classnumber <= 11)')])
    class Meta:
        table_name = "classes"


@snapshot.append
class Classrooms(peewee.Model):
    name = CharField(max_length=255)
    class Meta:
        table_name = "classrooms"


@snapshot.append
class Students(peewee.Model):
    fio = CharField(max_length=255)
    age = IntegerField(constraints=[SQL('CHECK (age >= 5)')])
    passwd = IntegerField()
    gender = BooleanField()
    class Meta:
        table_name = "students"


@snapshot.append
class ClassStudent(peewee.Model):
    studentID = snapshot.ForeignKeyField(index=True, model='students', on_delete='CASCADE')
    classID = snapshot.ForeignKeyField(index=True, model='classes', on_delete='CASCADE')
    class Meta:
        table_name = "classstudent"


@snapshot.append
class Teachers(peewee.Model):
    name = CharField(max_length=255)
    exp = IntegerField()
    passwd = IntegerField()
    class Meta:
        table_name = "teachers"


@snapshot.append
class Subjects(peewee.Model):
    name = CharField(max_length=255)
    class Meta:
        table_name = "subjects"


@snapshot.append
class TeacherSubject(peewee.Model):
    teacherID = snapshot.ForeignKeyField(index=True, model='teachers', on_delete='CASCADE')
    subjectID = snapshot.ForeignKeyField(index=True, model='subjects', on_delete='CASCADE')
    class Meta:
        table_name = "teachersubject"


@snapshot.append
class Timetable(peewee.Model):
    classID = snapshot.ForeignKeyField(index=True, model='classes', on_delete='CASCADE')
    classroomID = snapshot.ForeignKeyField(index=True, model='classrooms', on_delete='CASCADE')
    teacherAndSubjID = snapshot.ForeignKeyField(index=True, model='teachersubject', on_delete='CASCADE')
    lessonpos = IntegerField(constraints=[SQL('CHECK (lessonpos > 0)')])
    weekday = IntegerField(constraints=[SQL('CHECK (weekday >= 1 AND weekday <=6)')])
    year = IntegerField(constraints=[SQL('CHECK (year >= 1980)')])
    class Meta:
        table_name = "timetable"


@snapshot.append
class Lessons(peewee.Model):
    timetableID = snapshot.ForeignKeyField(index=True, model='timetable', on_delete='CASCADE')
    date = DateField()
    class Meta:
        table_name = "lessons"


@snapshot.append
class Marks(peewee.Model):
    studentID = snapshot.ForeignKeyField(index=True, model='students', on_delete='CASCADE')
    markvalue = IntegerField(constraints=[SQL('CHECK (markvalue >=1 AND markvalue <=5)')])
    lessonID = snapshot.ForeignKeyField(index=True, model='lessons', on_delete='CASCADE')
    class Meta:
        table_name = "marks"


@snapshot.append
class SubjectClass(peewee.Model):
    subjectID = snapshot.ForeignKeyField(index=True, model='subjects', on_delete='CASCADE')
    forclass = IntegerField(constraints=[SQL('CHECK (forclass >= 1 AND forclass <= 11)')])
    class Meta:
        table_name = "subjectclass"


def backward(old_orm, new_orm):
    admins = new_orm['admins']
    return [
        # Apply default value '' to the field admins.tmp
        admins.update({admins.tmp: ''}).where(admins.tmp.is_null(True)),
    ]
