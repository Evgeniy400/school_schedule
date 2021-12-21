from peewee import *


dbhandle = PostgresqlDatabase(
    database='postgres',
    user='postgres',
    password='322',
    host='localhost',
    port='5432'
)