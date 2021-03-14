from flask import Flask, render_template
from flaskext.mysql import MySQL

app = Flask(__name__)
mysql = MySQL()

app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'trees'
app.config['MYSQL_DATABASE_DB'] = 'space_missions'
app.config['MYSQL_DATABASE_HOST'] = '127.0.0.1'
mysql.init_app(app)

#Example Query
conn = mysql.connect()
cursor = conn.cursor()
query = '''select s.spaceship_name, d.destination_name, m.description

	from spaceships s, destinations d, missions m

	where s.sid = m.sid AND d.did = m.did;'''
cursor.execute(query)
data = []
for item in cursor:
	data.append(item)

print(data)




@app.route('/')
def index():
	return render_template('index.html', data = data)

@app.route('/hello/')
def hello():
	return 'hello'
