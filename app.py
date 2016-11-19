######################################
# author ben lawson <balawson@bu.edu> 
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
import flask.ext.login as flask_login
import datetime

#for image uploading from werkzeug import secure_filename
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'ESHhit'
app.config['MYSQL_DATABASE_DB'] = 'photome'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT Email from users")
users = cursor.fetchall()

def getUserList():
    cursor = conn.cursor()
    cursor.execute("SELECT Email from users")
    return cursor.fetchall()

class User(flask_login.UserMixin):
    pass

@login_manager.user_loader
def user_loader(email):
    users = getUserList()
    if not(email) or email not in str(users):
        return
    user = User()
    user.id = email
    return user

@login_manager.request_loader
def request_loader(request):
    users = getUserList()
    email = request.form.get('email')
    if not(email) or email not in str(users):
        return
    user = User()
    user.id = email
    cursor = mysql.connect().cursor()
    cursor.execute("SELECT Password FROM users WHERE Email = '{0}'".format(email))
    data = cursor.fetchall()
    pwd = str(data[0][0] )
    user.is_authenticated = request.form['password'] == pwd
    return user

class tagtrends:
    def __init__(self,text,picid,c):
        self.tag_text = text
        self.photo_id = picid
        self.count = c

class comments:
    def __init__(self,com,name):
        self.comment=com
        self.uname=name

class friend:
    def __init__(self,user,first,last,emailid):
        self.userid = user
        self.fname = first
        self.lname = last
        self.email = emailid

class photo:
    def __init__(self,pic,photo_id,caption,User_Id,album_id,t,l):
        self.albumid=album_id
        self.photoid=photo_id
        self.caption=caption
        self.pic=pic
        self.userid=User_Id
        self.tags = t
        self.likes=l

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
    return new_page_html
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
    if flask.request.method == 'GET':
        return '''
               <form action='login' method='POST'>
                <input type='text' name='email' id='email' placeholder='email'></input>
                <input type='password' name='password' id='password' placeholder='password'></input>
                <input type='submit' name='submit'></input>
               </form></br>
	       <a href='/'>Home</a>
               '''
    #The request method is POST (page is recieving data)
    email = flask.request.form['email']
    cursor = conn.cursor()
    #check if email is registered
    if cursor.execute("SELECT Password FROM users WHERE Email = '{0}'".format(email)):
        data = cursor.fetchall()
        pwd = str(data[0][0] )
        if flask.request.form['password'] == pwd:
            user = User()
            user.id = email
            flask_login.login_user(user) #okay login in user
            return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

    #information did not match
    return "<a href='/login'>Try again</a>\
            </br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
    flask_login.logout_user()
    return render_template('hello.html', message='Logged out') 

@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template('unauth.html') 

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
    return render_template('register.html', supress='True')  

@app.route("/register", methods=['POST'])
def register_user():
    try:
        first_name=request.form.get('first_name')
        last_name=request.form.get('last_name')
        email=request.form.get('email')
        password=request.form.get('password')
        dob=request.form.get('dob')
        hometown=request.form.get('hometown')
        gender=request.form.get('gender')
    except:
        print "couldn't find all tokens" #this prints to shell, end users will not see this (all print statements go to shell)
        return flask.redirect(flask.url_for('register'))
    cursor = conn.cursor()
    test =  isEmailUnique(email)
    if test:
        print cursor.execute("INSERT INTO users (First_Name, Last_Name, Email, Date_of_Birth, Hometown, Gender, Password) "
                             "VALUES ('{0}', '{1}' ,'{2}' ,'{3}' , '{4}' , '{5}', '{6}')".
                             format(first_name, last_name,email, dob, hometown, gender, password))
        conn.commit()
        #log user in
        user = User()
        user.id = email
        flask_login.login_user(user)
        return render_template('hello.html', name=first_name, message='Account Created!')
    else:
        print "couldn't find all tokens"
        return flask.redirect(flask.url_for('register'))

def getUsersPhotos(uid):
    cursor = conn.cursor()
    cursor.execute("SELECT pics, photo_id FROM photos WHERE User_id = '{0}'".format(uid))
    return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

def getAlbumPhotos(album_id):
    cursor = conn.cursor()
    #cursor.execute("SELECT pics,photo_id,caption,User_Id,album_id FROM photos WHERE album_id = '{0}'".format(album_id))
    cursor.execute("SELECT photo_id FROM photos WHERE album_id = '{0}'".format(album_id))
    photo_id_rows = cursor.fetchall()
    photo_list = []
    tags=[]
    likes=[]
    for row in photo_id_rows:
        cursor.execute("SELECT tag_text FROM tags WHERE photo_id='{0}'".format(row[0]))
        tags_row = cursor.fetchall()
        tag = ""
        for t_row in tags_row:
            tag = tag +" "+t_row[0]
        tags.append(tag)

        cursor.execute("SELECT photo_id,COUNT(photo_id) FROM likes WHERE photo_id='{0}' GROUP BY photo_id".format(row[0]))
        like_row = cursor.fetchall()
        if(like_row):
            for l_row in like_row:
                if(l_row[0] == row[0]):
                    likes.append(l_row[1])
                else:
                    likes.append(0)
        else:
            likes.append(0)

    cursor.execute("SELECT pics,photo_id,caption,User_Id,album_id FROM photos WHERE album_id = '{0}'".format(album_id))
    i = 0
    for photos in cursor:
        if(likes):
            temp_photo = photo(photos[0],photos[1],photos[2],photos[3],photos[4],tags[i],likes[i])
        else:
            temp_photo = photo(photos[0],photos[1],photos[2],photos[3],photos[4],tags[i],0)
        photo_list.append(temp_photo)
        i = i+1

    return photo_list

def getUserAlbums(uid):
    cursor = conn.cursor()
    cursor.execute("SELECT album_id,album_name FROM albums WHERE User_id = '{0}'".format(uid))
    return cursor.fetchall()


def getUserIdFromEmail(email):
    cursor = conn.cursor()
    cursor.execute("SELECT User_id  FROM users WHERE Email = '{0}'".format(email))
    return cursor.fetchone()[0]

def isEmailUnique(email):
    #use this to check if a email has already been registered
    cursor = conn.cursor()
    if cursor.execute("SELECT Email  FROM users WHERE Email = '{0}'".format(email)):
        #this means there are greater than zero entries with that email
        return False
    else:
        return True
#end login code

@app.route('/profile')
@flask_login.login_required
def protected():
    return render_template('hello.html', name=flask_login.current_user.id, message="Here's your profile")

#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML 
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
    if request.method == 'POST':
        uid = getUserIdFromEmail(flask_login.current_user.id)
        imgfile = request.files['file']
        album_id=request.form.get('album_id')
	photo_data = base64.standard_b64encode(imgfile.read())
        caption=request.form.get('caption')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO photos (album_id,caption, pics, User_id) VALUES ('{0}', '{1}', '{2}','{3}')".format(album_id,caption,photo_data,uid))
        conn.commit()
	return render_template('album_pics.html', name=flask_login.current_user.id, message='Photo uploaded!', photos=getUsersPhotos(album_id) )
    #The method is GET so we return a  HTML form to upload the a photo.
    return '''
        <!doctype html>
        <title>Upload new Picture</title>
        <h1>Upload new Picture</h1>
        <form action="" method=post enctype=multipart/form-data>
        <p><input type=file name=file>
        <input type=submit value=Upload>
        </form></br>
	<a href='/'>Home</a>
        '''
#end photo uploading code

@app.route('/upload_photos', methods=['GET','POST'])
@flask_login.login_required
def upload_photos():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    imgfile = request.files['photo']
    album_id=request.form.get('album_id')
    photo_data = base64.standard_b64encode(imgfile.read())
    caption=request.form.get('caption')
    tags=[]
    tags = request.form.get('tags').split(',')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO photos (album_id,caption, pics, User_id) VALUES ('{0}', '{1}', '{2}','{3}')".format(album_id,caption,photo_data,uid))
    photo_id = cursor.lastrowid
    for t in tags:
        cursor.execute("INSERT INTO tags (tag_text,photo_id) VALUES('{0}','{1}')".format(t,photo_id))
    conn.commit()
    return render_template('album_pics.html', name=flask_login.current_user.id, photos=getAlbumPhotos(album_id),album_id=album_id)


def display_friends():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    friend_list = []
    all_friends = []
    cursor = conn.cursor()
    cursor.execute("SELECT friends_Id FROM friends WHERE User_Id='{0}'".format(uid))
    friend_row = cursor.fetchall()
    for row in friend_row:
        friend_list.append(row[0])
    for eachfriend in friend_list:
        cursor.execute("SELECT First_Name,Last_Name,Email FROM users WHERE User_Id='{0}'".format(eachfriend))
        temp_friends = cursor.fetchall()
        for row_temp in temp_friends:
            temp = friend(eachfriend,row_temp[0],row_temp[1],row_temp[2])
            all_friends.append(temp)
    return all_friends

@app.route('/friends')
@flask_login.login_required
def add_friend():
    return render_template('friends.html',yourFriends=display_friends())

@app.route('/getfriends', methods=['GET', 'POST'])
@flask_login.login_required
def friend_lookup():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    name = request.form.get('friend_name')
    cursor = conn.cursor()
    cursor.execute("SELECT User_Id, first_name,last_name,Email FROM users WHERE first_name LIKE '"+name+"%' OR last_name LIKE '"+name+"%' AND User_Id<>'{0}' AND User_Id NOT IN(SELECT friends_Id FROM friends WHERE User_Id = '{0}') ".format(uid))
    friend_list = []
    for friends in cursor:
        temp_friend = friend(friends[0],friends[1],friends[2],friends[3])
        friend_list.append(temp_friend)
    return render_template('friends.html',friends=friend_list,yourFriends=display_friends())

@app.route('/friends_inlist', methods=['GET','POST'])
@flask_login.login_required
def addin_friendlist():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    friend_uid = request.form.get('uid')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO friends(User_Id,friends_Id)""VALUE ('{0}','{1}')".format(uid,friend_uid))
    conn.commit()
    return render_template('friends.html',yourFriends=display_friends())

@app.route('/album')
@flask_login.login_required
def navigate_album():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    return render_template('album.html',user_album = getUserAlbums(uid))

@app.route('/display_album', methods=['GET', 'POST'])
@flask_login.login_required
def display_album():
    #uid = getUserIdFromEmail(flask_login.current_user.id)
    album_id = request.args.get('album_id')
    # cursor = conn.cursor()
    # album_name = cursor.execute("SELECT album_name FROM albums WHERE album_id='{0}'".format(album_id))
    # conn.commit()
    return render_template('album_pics.html',album_id=album_id,photos=getAlbumPhotos(album_id))

@app.route('/create_album', methods=['GET', 'POST'])
@flask_login.login_required
def create_album():
    album_name = request.form.get('album_name')
    uid = getUserIdFromEmail(flask_login.current_user.id)
    date = datetime.datetime.now().date()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO albums(User_Id,album_name, date_of_creation)""VALUE('{0}','{1}','{2}')".format(uid,album_name,date))
    album_id=cursor.lastrowid
    #album_id=cursor.execute("SELECT album_id FROM albums where album_name='{0}' AND User_Id='{1}' AND date_of_creation='{2}'".format(album_name,uid,date))
    conn.commit()
    return render_template('album_pics.html',album_name=album_name,album_id=album_id)

@app.route('/display_by_tags', methods=['GET', 'POST'])
@flask_login.login_required
def navigate_photos_by_tags():
    return render_template('tag_photos.html')

@app.route('/photos_by_tags', methods=['GET', 'POST'])
@flask_login.login_required
def photos_by_tags():
    tag_search = request.form.get('tag_search')
    cursor = conn.cursor()
    cursor.execute("SELECT photo_id FROM tags WHERE tag_text = '{0}'".format(tag_search))
    photo_id_rows = cursor.fetchall()
    tags=[]
    photo_list=[]
    photo_ids = []
    likes = []
    for row in photo_id_rows:
        photo_ids.append(row[0])
        cursor.execute("SELECT tag_text FROM tags WHERE photo_id='{0}' ".format(row[0]))
        tags_row = cursor.fetchall()
        tag= ""
        for t_row in tags_row:
            tag = tag +" "+t_row[0]
        tags.append(tag)

        cursor.execute("SELECT photo_id,COUNT(photo_id) FROM likes GROUP BY photo_id")
        like_row = cursor.fetchall()
        for l_row in like_row:
            if(l_row[0] == row[0]):
                likes.append(l_row[1])
            else:
                likes.append(0)

    for id in photo_ids:
        cursor.execute("SELECT pics,photo_id,caption,User_Id,album_id FROM photos WHERE photo_id = '{0}'".format(id))
        i = 0
        for tagged_photo in cursor:
            temp_photo = photo(tagged_photo[0],tagged_photo[1],tagged_photo[2],tagged_photo[3],tagged_photo[4],tags[i],likes[i])
            photo_list.append(temp_photo)
            i = i+1
    return render_template('tag_photos.html',photos=photo_list)

@app.route('/add_like', methods=['GET', 'POST'])
@flask_login.login_required
def add_like():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    album_id = request.form.get('album_id')
    photo_id = request.form.get('photo_id')
    cursor = conn.cursor()
    cursor.execute("SELECT photo_id,User_Id FROM likes WHERE photo_id = '{0}' AND User_Id = '{1}'".format(photo_id,uid))
    flag = cursor.fetchall()
    if(flag):
        msg = "You have already liked the picture"
    else:
        msg = "successfully liked"
        cursor.execute("INSERT INTO likes (photo_id,User_Id,album_id) VALUE('{0}','{1}','{2}') ".format(photo_id,uid,album_id))
        conn.commit()
    return render_template('album_pics.html', photos = getAlbumPhotos(album_id), message = msg)

@app.route('/add_all_like', methods=['GET', 'POST'])
@flask_login.login_required
def add_all_like():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    photo_id = request.form.get('photo_id')
    album_id = request.form.get('album_id')
    cursor = conn.cursor()
    cursor.execute("SELECT photo_id,User_Id FROM likes WHERE photo_id = '{0}' AND User_Id = '{1}'".format(photo_id,uid))
    flag = cursor.fetchall()
    if(flag):
        msg = "You have already liked the picture"
    else:
        msg = "successfully liked"
        cursor.execute("INSERT INTO likes (photo_id,User_Id,album_id) VALUE('{0}','{1}','{2}') ".format(photo_id,uid,album_id))
        conn.commit()
    photo_list=get_photo_list()
    return render_template('browse.html', photos = photo_list)

def get_photo_list():
    cursor=conn.cursor()
    cursor.execute("SELECT photo_id FROM photos ")
    photo_id_rows=cursor.fetchall()
    photo_list=[]
    tags=[]
    likes=[]
    for row in photo_id_rows:
        cursor.execute("SELECT tag_text FROM tags WHERE photo_id='{0}'".format(row[0]))
        tags_row=cursor.fetchall()
        tag=""
        for t_row in tags_row:
            tag=tag+" "+t_row[0]
        tags.append(tag)

        cursor.execute("SELECT photo_id,COUNT(photo_id) FROM likes WHERE photo_id='{0}' GROUP BY photo_id".format(row[0]))
        like_row = cursor.fetchall()
        if(like_row):
            for l_row in like_row:
                if(l_row[0] == row[0]):
                    likes.append(l_row[1])
                else:
                    likes.append(0)
        else:
            likes.append(0)
    cursor.execute("SELECT pics,photo_id,caption,User_Id,album_id FROM photos ")
    i=0
    for photos in cursor:
        if(likes):
            temp_photo = photo(photos[0],photos[1],photos[2],photos[3],photos[4],tags[i],likes[i])
        else:
            temp_photo = photo(photos[0],photos[1],photos[2],photos[3],photos[4],tags[i],0)
        photo_list.append(temp_photo)
        i = i+1
    return photo_list

@app.route('/all', methods=['GET', 'POST'])
def all_pics():
    return render_template('browse.html')

@app.route('/browse_pics', methods=['GET', 'POST'])
def browse_pics():
    photo_list = get_photo_list()
    return render_template('browse.html', photos=photo_list)

@app.route('/navigate_comment', methods=['GET', 'POST'])
def navigate_comment():
    #uid = getUserIdFromEmail(flask_login.current_user.id)
    photo_id=request.form.get('photo_id')
    user_comments=[]
    cursor=conn.cursor()
    cursor.execute("SELECT pics FROM photos WHERE photo_id='{0}'".format(photo_id))
    for pic_temp in cursor.fetchall():
        pic = pic_temp[0]
    cursor.execute("SELECT comment_text,user_name FROM comments WHERE photo_id='{0}'".format(photo_id))
    comment_row = cursor.fetchall()
    for c_row in comment_row:
        temp_comment = comments(c_row[0],c_row[1])
        user_comments.append(temp_comment)
    return render_template('comment.html', picture=pic,photo_id=photo_id,comments=user_comments)

@app.route('/add_comment', methods=['GET', 'POST'])
def add_comment():
    user_comments=[]
    photo_id=request.form.get('photo_id')
    comment = request.form.get('comment')
    cursor=conn.cursor()
    cursor.execute("SELECT pics,User_Id FROM photos WHERE photo_id='{0}'".format(photo_id))
    for pic_temp in cursor.fetchall():
        pic = pic_temp[0]
        pic_user = pic_temp[1]
    try:
        uid = getUserIdFromEmail(flask_login.current_user.id)
        cursor.execute("SELECT First_Name FROM users WHERE User_Id='{0}'".format(uid))
        uname=cursor.fetchall()
        for u_temp in uname:
            user_fname = u_temp[0]
    except:
        uid = 0
        user_fname = "Anonymous"
    if(uid == 0 or pic_user!=uid):
        cursor.execute("INSERT INTO comments(User_id,comment_text,photo_id,user_name) VALUE('{0}','{1}','{2}','{3}')".format(uid,comment,photo_id,user_fname))
        conn.commit()
        message = ""
    else:
        message = "you cannot comment on your own pics"

    cursor.execute("SELECT comment_text,user_name FROM comments WHERE photo_id='{0}'".format(photo_id))
    comment_row = cursor.fetchall()
    for c_row in comment_row:
        temp_comment = comments(c_row[0],c_row[1])
        user_comments.append(temp_comment)

    return render_template('comment.html',comments=user_comments,picture=pic,photo_id=photo_id,message=message)

@app.route('/delete_photo', methods=['GET', 'POST'])
@flask_login.login_required
def delete_photo():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    photo_id=request.form.get('photo_id')
    album_id = request.form.get('album_id')
    cursor=conn.cursor()
    cursor.execute("DELETE FROM photos WHERE photo_id='{0}'".format(photo_id))
    conn.commit()
    return render_template('album_pics.html',album_id=album_id,photos=getAlbumPhotos(album_id))

@app.route('/toptags', methods=['GET', 'POST'])
@flask_login.login_required
def toptags():
    trending_tags = []
    cursor=conn.cursor()
    cursor.execute("SELECT tag_text,photo_id, COUNT(tag_text) FROM tags GROUP BY(tag_text) ORDER BY COUNT(tag_text) DESC limit 10")
    trending = cursor.fetchall()
    for trends in trending:
        temp_tags = tagtrends(trends[0],trends[1],trends[2])
        trending_tags.append(temp_tags)
    return render_template('top10tags.html',tag_trends=trending_tags)

@app.route('/topusers', methods=['GET', 'POST'])
@flask_login.login_required
def topusers():
    topusers = []
    cursor=conn.cursor()
    cursor.execute("SELECT User_Id, COUNT(User_Id) FROM photos GROUP BY(User_Id) ORDER BY COUNT(User_Id) DESC limit 10")
    trending=cursor.fetchall()
    for trends in trending:
        topusers.append(trends[0])
    return render_template('top10users.html',user_trends=topusers)

#default page  
@app.route("/", methods=['GET'])
def hello():
    return render_template('hello.html', message='Welcome to Photoshare')


if __name__ == "__main__":
    #this is invoked when in the shell  you run 
    #$ python app.py 
    app.run(port=5000, debug=True)
