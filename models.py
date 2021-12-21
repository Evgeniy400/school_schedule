from connect import *


class BaseModel(Model):
    class Meta:
        database = dbhandle


class Admins(BaseModel):
    id = AutoField()
    passwd = IntegerField()


class Students(BaseModel):
    id = AutoField()
    fio = CharField(null=False)
    age = IntegerField(constraints=[Check('age >= 5')])
    passwd = IntegerField()
    gender = BooleanField()



class Classes(BaseModel):
    id = AutoField()
    year = IntegerField(constraints=[Check('year >= 1980')])
    classChar = CharField(null=False, max_length=1, default='')
    classnumber = IntegerField(constraints=[Check('classnumber >= 1 AND classnumber <= 11')])



class ClassStudent(BaseModel):
    id = AutoField()
    studentID = ForeignKeyField(model=Students, on_delete='CASCADE')
    classID = ForeignKeyField(model=Classes, on_delete='CASCADE')


class Classrooms(BaseModel):
    id = AutoField()
    name = CharField(null=False)


class Teachers(BaseModel):
    id = AutoField()
    name = CharField(null=False)
    exp = IntegerField(null=False)
    passwd = IntegerField()


class Subjects(BaseModel):
    id = AutoField()
    name = CharField(null=False)


class SubjectClass(BaseModel):
    id = AutoField()
    subjectID = ForeignKeyField(model=Subjects, on_delete='CASCADE')
    forclass = IntegerField(constraints=[Check('forclass >= 1 AND forclass <= 11')])


class TeacherSubject(BaseModel):
    id = AutoField()
    teacherID = ForeignKeyField(model=Teachers, on_delete='CASCADE')
    subjectID = ForeignKeyField(model=Subjects, on_delete='CASCADE')


class Timetable(BaseModel):
    id = AutoField()
    classID = ForeignKeyField(model=Classes, on_delete='CASCADE')
    classroomID = ForeignKeyField(model=Classrooms, on_delete='CASCADE')
    teacherAndSubjID = ForeignKeyField(model=TeacherSubject, on_delete='CASCADE')
    lessonpos = IntegerField(constraints=[Check('lessonpos > 0')])
    weekday = IntegerField(constraints=[Check('weekday >= 1 AND weekday <=6')])
    year = IntegerField(constraints=[Check('year >= 1980')])


class Lessons(BaseModel):
    id = AutoField()
    timetableID = ForeignKeyField(model=Timetable, on_delete='CASCADE')
    date = DateField(null=False)


class Marks(BaseModel):
    id = AutoField()
    studentID = ForeignKeyField(model=Students, on_delete='CASCADE', null=False)
    markvalue = IntegerField(constraints=[Check('markvalue >=1 AND markvalue <=5')])
    lessonID = ForeignKeyField(model=Lessons, on_delete='CASCADE')

