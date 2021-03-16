######################################
# author ben lawson <balawson@bu.edu>
# Edited by: Craig Einstein <einstein@bu.edu>
######################################
# Some code adapted from
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
from config import password
import flask_login

# for image uploading
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = "super secret string"  # Change this!

# These will need to be changed according to your creditionals
app.config["MYSQL_DATABASE_USER"] = "root"
app.config["MYSQL_DATABASE_PASSWORD"] = password()
app.config["MYSQL_DATABASE_DB"] = "photoshare"
app.config["MYSQL_DATABASE_HOST"] = "localhost"
mysql.init_app(app)

# begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users")
users = cursor.fetchall()


def getUserList():
    cursor.execute("SELECT email from Users")
    return cursor.fetchall()


class User(flask_login.UserMixin):
    pass


@login_manager.user_loader
def user_loader(email):
    users = getUserList()
    if not (email) or email not in str(users):
        return
    user = User()
    cursor = mysql.connect().cursor()
    cursor.execute("SELECT user_id FROM Users WHERE email = '{0}'".format(email))
    data = cursor.fetchall()
    user.id = str(data[0][0])
    # print("in user_loader user id", user.id)
    return user


@login_manager.request_loader
def request_loader(request):
    users = getUserList()
    email = request.form.get("email")
    if not (email) or email not in str(users):
        return
    user = User()
    # user.id = getUserIdFromEmail(email)
    cursor = mysql.connect().cursor()
    cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
    data = cursor.fetchall()
    pwd = str(data[0][0])
    cursor.execute("SELECT user_id FROM Users WHERE email = '{0}'".format(email))
    data = cursor.fetchall()
    user.id = str(data[0][0])
    # print("in user_loader user id", user.id)
    user.is_authenticated = request.form["password"] == pwd
    return user


"""
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
"""


@app.route("/login", methods=["GET", "POST"])
def login():
    if flask.request.method == "GET":
        return """
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   """
    # The request method is POST (page is recieving data)
    email = flask.request.form["email"]
    cursor = conn.cursor()

    # check if email is registered
    if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
        data = cursor.fetchall()
        pwd = str(data[0][0])
        if flask.request.form["password"] == pwd:
            user = User()
            user.id = email
            flask_login.login_user(user)  # okay login in user
            return flask.redirect(
                flask.url_for("protected")
            )  # protected is a function defined in this file

    # information did not match
    return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"


@app.route("/logout")
def logout():
    flask_login.logout_user()
    return render_template("hello.html", message="Logged out")


@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template("unauth.html")


# you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=["GET"])
def register():
    return render_template("register.html", supress="True")


@app.route("/register", methods=["POST"])
def register_user():
    # tests to see if all required fields (first,last names, password, email, dob) were filled
    # for optional field, only bday gives problems if empty
    try:
        email = request.form.get("email")
        password = request.form.get("password")
        first_name = request.form.get("first-name")
        last_name = request.form.get("last-name")
        dob = request.form.get("birthday")
        home = request.form.get("hometown")
        gender = request.form.get("gender")
    except:
        print(
            "couldn't find all tokens"
        )  # this prints to shell, end users will not see this (all print statements go to shell)
        return flask.redirect(flask.url_for("register"))
    cursor = conn.cursor()
    test = isEmailUnique(email)
    # if email is unique
    if test:
        # create a new user id, 1 greater than previous max
        cursor.execute("SELECT MAX(user_id) FROM Users")
        id_value = cursor.fetchone()[0]
        if id_value is not None:
            user_id = id_value + 1
        else:
            user_id = 0
        print(
            cursor.execute(
                "INSERT INTO Users (user_id, first_name, last_name, email, password, hometown, gender) VALUES ('{0}', '{1}','{2}','{3}','{4}','{5}','{6}')".format(
                    user_id,
                    first_name,
                    last_name,
                    email,
                    password,
                    home,
                    gender,
                )
            )
        )
        conn.commit()
        if dob != "":
            cursor.execute(
                "UPDATE Users SET birth_date = '{0}' WHERE user_id = '{1}'".format(
                    dob, user_id
                )
            )
        conn.commit()
        # log user in
        user = User()
        user.id = user_id
        flask_login.login_user(user)
        cursor.execute(
            "SELECT first_name FROM Users WHERE user_id = '{0}'".format(user_id)
        )
        first = cursor.fetchone()[0]
        return render_template("hello.html", name=first, message="Account Created!")
    else:
        print("couldn't find all tokens")
        return flask.redirect(flask.url_for("register"))


def getUsersPhotos(uid):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT data, photo_id, caption FROM Photos WHERE user_id = '{0}'".format(uid)
    )
    return cursor.fetchall()  # NOTE list of tuples, [(imgdata, pid), ...]


def getUsersAlbums(uid):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name, albums_id FROM Albums WHERE user_id = '{0}'".format(uid)
    )
    return cursor.fetchall()


def getUserIdFromEmail(email):
    cursor = conn.cursor()
    cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
    return cursor.fetchone()[0]


# def getTopUsers():
#     cursor = conn.cursor()
#     cursor.execute(
#         "SELECT first_name, last_name FROM Users WHERE SUM(SELECT( COUNT(comment_id) FROM Comments WHERE Comments.user_id = User.user_id)  ) "
#     )


def isEmailUnique(email):
    # use this to check if a email has already been registered
    cursor = conn.cursor()
    if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)):
        # this means there are greater than zero entries with that email
        return False
    else:
        return True


# end login code


@app.route("/profile")
@flask_login.login_required
def protected():
    print("in protected user id = ", flask_login.current_user.id)
    uid = flask_login.current_user.id
    cursor.execute("SELECT first_name  FROM Users WHERE user_id = '{0}'".format(uid))
    first = cursor.fetchone()[0]
    print("first name = ", first)
    return render_template(
        "hello.html",
        name=first,
        message="Here's your profile",
        photos=getUsersPhotos(uid),
        albums=getUsersAlbums(uid)
        # topUsers=getTopUsers(),
    )


# begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML
ALLOWED_EXTENSIONS = set(["png", "jpg", "jpeg", "gif"])


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1] in ALLOWED_EXTENSIONS


@app.route("/upload", methods=["GET", "POST"])
@flask_login.login_required
def upload_file():
    if request.method == "POST":
        # uid = getUserIdFromEmail(flask_login.current_user.id)
        uid = flask_login.current_user.id
        cursor = conn.cursor()
        imgfile = request.files["photo"]
        imgfile = request.files["photo"]
        caption = request.form.get("caption")
        albums_name = request.form.get("album")
        photo_data = base64.b64encode(imgfile.read())
        cursor.execute("SELECT MAX(photo_id) FROM Photos")
        
        id_value = cursor.fetchone()[0]
        if id_value is not None:
            photo_id = id_value + 1
        else:
            photo_id = 0

        # if the user doesn't own an album of that name, create a new one
        if not cursor.execute(
            "SELECT albums_id FROM albums WHERE name = '{0}' and user_id = '{1}'".format(
                albums_name, uid
            )
        ):
            cursor.execute("SELECT MAX(albums_id) FROM Albums")
            id_value = cursor.fetchone()[0]
            if id_value is not None:
                albums_id = id_value + 1
            else:
                albums_id = 0
            cursor.execute(
                "INSERT INTO Albums (albums_id, user_id, name) VALUES (%s, %s, %s)",
                (albums_id, uid, albums_name),
            )
            conn.commit()

        cursor.execute(
            "SELECT albums_id FROM albums WHERE name = '{0}' and user_id = '{1}'".format(
                albums_name, uid
            )
        )
        albums_id = cursor.fetchone()[0]
        cursor.execute(
            """INSERT INTO Photos (data, user_id, caption, photo_id, albums_id) VALUES (%s, %s, %s, %s, %s )""",
            (photo_data, uid, caption, photo_id, albums_id),
        )
        conn.commit()
        return render_template(
            "hello.html",
            name=flask_login.current_user.id,
            message="Photo uploaded!",
            photos=getUsersPhotos(uid),
            albums=getUsersAlbums(uid),
            base64=base64,
        )
    # The method is GET so we return a  HTML form to upload the a photo.
    else:
        return render_template("upload.html")


# end photo uploading code

# user's friends page
@app.route("/friends", methods=["GET", "POST"])
@flask_login.login_required
def find_friends():
    cursor.execute(
        "SELECT first_name  FROM Users WHERE user_id = '{0}'".format(
            flask_login.current_user.id
        )
    )
    first = cursor.fetchone()[0]
    cursor.execute(
        "SELECT user_id2  FROM Friends WHERE user_id1 = '{0}'".format(
            flask_login.current_user.id
        )
    )
    friends = cursor.fetchall()
    return render_template("friends.html", name=first, friends=friends)

def getName(uid,key="user_id",value="first_name",table="Users"):
    cursor.execute(
        "SELECT {2} FROM {3} WHERE {1} = '{0}'".format(
            flask_login.current_user.id, key,value, table
        )
    )
    return cursor.fetchone()[0]

# All photos
@app.route("/photos", methods=["GET", "POST"])
# @flask_login.login_required
def getAllPhotos():
    cursor = conn.cursor()
    cursor.execute(
        "SELECT data, photo_id, caption FROM Photos".format()
    )
    allPhotos = cursor.fetchall()  # NOTE list of tuples, [(imgdata, pid), ...]

    userPhotos = ""
    uname = ""
    
    if (flask_login.current_user.is_authenticated):
        uid = flask_login.current_user.id
        uname = getName(uid)
        userPhotos = getUsersPhotos(uid)

    if len(allPhotos)>0:
        return render_template("photos.html",name=uname, photos=allPhotos, myPhotos= userPhotos)

    return render_template("photos.html",name=uname, photos = "")


#Albums
def getPhotosInAlbums(aid):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT data, photo_id, caption FROM Photos WHERE albums_id = '{0}'".format(aid)
    )
    return cursor.fetchall()

@app.route("/albums", methods=["GET", "POST"])
# @flask_login.login_required
def getAllAblums():
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name, albums_id, user_id FROM Albums".format()
    )
    allAblums = cursor.fetchall()  # NOTE list of tuples, [(imgdata, pid), ...]
    allAlbumPhotos = [(x[0],getPhotosInAlbums(x[1])) for x in allAblums]
    userAlbums = ""
    uname = "" 
    
    if (flask_login.current_user.is_authenticated):
        uid = flask_login.current_user.id
        uname = getName(uid)
        userAlbums = getUsersAlbums(uid)
        userAlbumsPhotos = [(x[0], getPhotosInAlbums(x[1])) for x in userAlbums]

    if len(allAblums) > 0:
        return render_template("albums.html", name=uname, albums=allAlbumPhotos, myAlbums=userAlbumsPhotos)

    return render_template("albums.html", name=uname, albums="")
# default page
@app.route("/", methods=["GET"])
def hello():
    return render_template("hello.html", message=None)


if __name__ == "__main__":
    # this is invoked when in the shell  you run
    # $ python app.py
    app.run(port=5000, debug=True)
