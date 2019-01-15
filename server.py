from flask import Flask, render_template, request, g, make_response, jsonify
from flask_cors import CORS
import sqlite3 as sql
import json
from werkzeug import secure_filename
from deepspeaker.unseen_speakers import MultithreadsInference
from deepspeaker.audio_reader import AudioReader
import os

app = Flask(__name__)
CORS(app)

audio_reader = AudioReader()
ds_inference = MultithreadsInference(audio_reader=audio_reader)


# api get all personnel
@app.route('/api/personnel', methods = ['GET'])
def personnel():
	if request.method == 'GET':
		con = sql.connect("database.db")
		con.row_factory = sql.Row   
		cur = con.cursor()
		cur.execute("select * from personnel")
		rows = cur.fetchall();
		psn={
		'personnel':[]
		}

		for row in rows:
			psn['personnel'].append({
				'id':row['id'],
				'ava_url': row['ava_url'],
				'name':row['name'],
				'phone': row['phone'],
				'email':row['email'],
				'position':row['position'],
				'part': row['part'],
				'sounds':row['sounds']
				})
		con.close()
		return json.dumps(psn)


# api post a personnel
@app.route('/api/personnel',methods=['POST'])
def add_person():
	if request.method == 'POST':
		ava_url=request.json['ava_url']
		name=request.json['name']
		phone=request.json['phone']
		email=request.json['email']
		position=request.json['position']
		part=request.json['part']
		sounds=request.json['sounds']

		with sql.connect("database.db") as con:
			cur = con.cursor()
			cur.execute("INSERT INTO personnel (ava_url,name,phone,email,position,part,sounds) VALUES (?,?,?,?,?,?,?)",(ava_url,name,phone,email,position,part,sounds))
			con.commit()
		return "Person Added"


# api put a person
@app.route('/api/personnel/id=<int:id>',methods=['PUT'])
def put_person(id):
	if request.method == 'PUT':
		ava_url=request.json['ava_url']
		name=request.json['name']
		phone=request.json['phone']
		email=request.json['email']
		position=request.json['position']
		part=request.json['part']
		sounds=request.json['sounds']

		with sql.connect("database.db") as con:
			cur = con.cursor()
			cur.execute("UPDATE personnel SET ava_url=?,name=?,phone=?,email=?,position=?,part=?,sounds=? WHERE id=?",(ava_url,name,phone,email,position,part,sounds, id))
			con.commit()

		return "Person Changed"


# api delete a person
@app.route('/api/personnel/id=<int:id>',methods=['DELETE'])
def del_person(id):
	if request.method == 'DELETE':
		with sql.connect("database.db") as con:
			cur = con.cursor()
			cur.execute("DELETE FROM personnel WHERE id=%d" %id)
			con.commit()

		return "Person Deleted"


# api get all rooms
@app.route('/api/room', methods = ['GET'])
def room():
	if request.method == 'GET':
		con = sql.connect("database.db")
		con.row_factory = sql.Row   
		cur = con.cursor()
		cur.execute("SELECT * FROM room")

		rows = cur.fetchall();
		r = {
			'room': []
		}

		for row in rows:
			r['room'].append({
				'id':row['id'],
				'ava_url': row['ava_url'],
				'name':row['name'],
				'description':row['description']
				})
		con.close()
		return json.dumps(r)


# api post a room
@app.route('/api/room',methods=['POST'])
def add_room():
	if request.method == 'POST':
		ava_url=request.json['ava_url']
		name=request.json['name']
		description=request.json['description']
	
		with sql.connect("database.db") as con:
			cur = con.cursor()
			cur.execute("INSERT INTO room (ava_url,name,description) VALUES (?,?,?)",(ava_url,name,description))
			con.commit()

		return "Room Added"


# api put a room
@app.route('/api/room/id=<int:id>',methods=['PUT'])
def put_room(id):
	if request.method == 'PUT':
		ava_url=request.json['ava_url']
		name=request.json['name']
		description=request.json['description']
	
		with sql.connect("database.db") as con:
			cur = con.cursor()
			cur.execute("UPDATE room SET ava_url=?,name=?,description=? WHERE id=?",(ava_url,name,description, id))
			con.commit()

		return "Room Changed"


# api delete a room
@app.route('/api/room/id=<int:id>',methods=['DELETE'])
def del_room(id):
	if request.method == 'DELETE':
		with sql.connect("database.db") as con:
			cur = con.cursor()
			cur.execute("DELETE FROM room WHERE id=%d" %id)
			con.commit()

		return "Room Deleted"


# api get all meeting
@app.route('/api/meeting', methods = ['GET'])
def meeting():
	if request.method == 'GET':
		con = sql.connect("database.db")
		con.row_factory = sql.Row   
		cur = con.cursor()
		cur.execute("select * from meeting")
		rows = cur.fetchall();
		m = {
			'meeting': []
		}

		for row in rows:
			m['meeting'].append({
				'id':row['id'],
				'name':row['name'],
				'content':row['content'],
				'members': row['members'],
				'room_name': row['room_name'],
				'date_time': row['date_time'],
				'leader': row['leader'],
				'secretary': row['secretary']
				})
		con.close()
		return json.dumps(m)


# api create a meeting
@app.route('/api/meeting', methods=['POST'])
def add_meeting():
	if request.method == 'POST':
		name=request.json['name']
		content=request.json['content']
		members=request.json['members']
		room_name=request.json['room_name']
		date_time=request.json['date_time']
		leader=request.json['leader']
		secretary=request.json['secretary']

		with sql.connect("database.db") as con:
			cur = con.cursor()
			cur.execute("INSERT INTO meeting (name,content,members,room_name,date_time,leader,secretary) VALUES (?,?,?,?,?,?,?)",(name,content,members,room_name,date_time,leader,secretary))
			con.commit()

			return "Meeting Added"


# api put a meeting
@app.route('/api/meeting/id=<int:id>', methods=['PUT'])
def change_meeting(id):
	if request.method == 'PUT':
		name=request.json['name']
		content=request.json['content']
		members=request.json['members']
		room_name=request.json['room_name']
		date_time=request.json['date_time']
		leader=request.json['leader']
		secretary=request.json['secretary']

		with sql.connect("database.db") as con:
			cur = con.cursor()
			cur.execute("UPDATE meeting SET name=?,content=?,members=?,room_name=?,date_time=?,leader=?,secretary=? WHERE id=?",(name,content,members,room_name,date_time,leader,secretary, id))
			con.commit()

			return "Meeting Changed"


# api del a meeting
@app.route('/api/meeting/id=<int:id>', methods=['DELETE'])
def del_meeting(id):
	if request.method == 'DELETE':		
		with sql.connect("database.db") as con:
			cur = con.cursor()
			cur.execute("DELETE FROM meeting WHERE id=%d" %id)
			con.commit()

			return "Meeting Deleted"


# api get detail meeting by meetingId
@app.route('/api/detail_meeting/meeting_id=<int:id>', methods = ['GET'])
def detail(id):
	if request.method == 'GET':
		con = sql.connect("database.db")
		con.row_factory = sql.Row   
		cur = con.cursor()	
		cur.execute("select * from detail where meeting_id = %d" %id)
		rows = cur.fetchall();
		d = {
			'detail': []
		}

		for row in rows:
			d['detail'].append({
				'id':row['id'],
				'name':row['name'],
				'meeting_id':row['meeting_id'],
				'time': row['time'],
				'content': row['content']
				})
		con.close()
		return json.dumps(d)


# api them 1 loi thoai
@app.route('/api/detail_meeting/meeting_id=<int:id>', methods = ['POST'])
def add_detail(id):
	if request.method == 'POST':
		name=request.json['name']
		content=request.json['content']
		time=request.json['time']

		with sql.connect("database.db") as con:
			cur = con.cursor()
			cur.execute("INSERT INTO detail (name,content,time,meeting_id) VALUES (?,?,?,?)",(name,content,time,id))
			con.commit()

			return "Detail Added"


# api sua loi thoai
@app.route('/api/detail_meeting/meeting_id=<int:id>/id=<int:id2>', methods = ['PUT'])
def put_detail(id,id2):
	if request.method == 'PUT':
		name=request.json['name']
		content=request.json['content']
		time=request.json['time']

		with sql.connect("database.db") as con:
			cur = con.cursor()
			cur.execute("UPDATE detail SET name=?,content=?,time=? WHERE meeting_id=? AND id =?",(name,content,time,id,id2))
			con.commit()

			return "Detail Changed"


# api xoa loi thoai
@app.route('/api/detail_meeting/meeting_id=<int:id>/id=<int:id2>', methods = ['DELETE'])
def delete_detail(id,id2):
	if request.method == 'DELETE':
		with sql.connect("database.db") as con:
			cur = con.cursor()
			cur.execute("DELETE FROM detail WHERE meeting_id=? AND id =?",(id,id2))
			con.commit()

			return "Detail Deleted"


# api upload file
@app.route('/api/uploader', methods=['POST'])
def uploader_file():
	if request.method == 'POST':
		f = request.files['file']
		f.save(os.path.join('lkh', secure_filename(f.filename)))
		audio_path =os.getcwd() +"/"+ os.path.join('lkh', secure_filename(f.filename))
		r = os.popen('curl -X POST http://0.0.0.0:4000/transcribe -H "Content-type: multipart/form-data"' + ' -F "file=@"' + audio_path).read()
		return r


# api upload file
@app.route('/api/inference', methods=['POST'])
def inference():
	if request.method == 'POST':
		f = request.files['file']
		f.save(os.path.join('lkh', secure_filename(f.filename)))
		filename =os.getcwd() +"/"+ os.path.join('lkh', secure_filename(f.filename))
		# nhan dang ng noi
		result = ds_inference.run(filename)
		return make_response(jsonify({
			'status': 'success',
			'result': result
		})), 200


if __name__ == '__main__':
	app.run( host='0.0.0.0', port=5000, debug=True)
