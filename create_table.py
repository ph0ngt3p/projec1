import sqlite3

conn = sqlite3.connect('database.db')
print "Opened database successfully";

conn.execute('CREATE TABLE personnel (id INTEGER PRIMARY KEY, name TEXT, phone TEXT, email TEXT, ava_url TEXT, position TEXT, part TEXT, sounds TEXT)')
print "Table personnel created successfully";


conn.execute('CREATE TABLE room (id INTEGER PRIMARY KEY, ava_url TEXT, name TEXT, description TEXT)')
print "Table room created successfully"

conn.execute('CREATE TABLE meeting (id INTEGER PRIMARY KEY, name TEXT, content TEXT, members TEXT, room_name TEXT, date_time TEXT, leader TEXT, secretary TEXT)')
print "Table meeting created successfully"

conn.execute('CREATE TABLE detail ( meeting_id INTEGER, id INTEGER PRIMARY KEY, time TEXT, name TEXT, content TEXT)')
print "Table detail created successfully"
conn.close()