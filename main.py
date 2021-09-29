from flask import Flask, render_template, request, session, redirect
import mysql.connector
import pyrebase
from flask_mail import Mail
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import json
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import math
import os

with open('config.json', 'r') as c:
    params = json.load(c)["params"]

local_server = True
app = Flask(__name__)
app.secret_key = 'super-secret-key'
app.config['UPLOAD_FOLDER'] = params['upload_location']
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params['mail_user'],
    MAIL_PASSWORD=params['mail-password']
)
mail = Mail(app)
if local_server:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    firebase = pyrebase.initialize_app(params['prod_uri'])
    storage = firebase.storage()


db = SQLAlchemy(app)


class Contacts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(25), nullable=False)
    subject = db.Column(db.String(30), nullable=False)
    message = db.Column(db.String(120), nullable=True)
    date = db.Column(db.String(12), nullable=True)


class Signup(UserMixin, db.Model):
    name = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(30), nullable=False, primary_key=True)
    password = db.Column(db.String(25), nullable=False)
    con_pass = db.Column(db.String(25), nullable=False)


class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(25), nullable=False)
    title = db.Column(db.String(50), nullable=True)
    content = db.Column(db.String(120), nullable=True)
    file = db.Column(db.String, nullable=False)
    date = db.Column(db.String(12), nullable=True)


@login_manager.user_loader
def load_user(email):
    return Signup.query.get(email)


@app.route("/")
def hello():
    return render_template('index.html', params=params)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if 'email' in session and session['email'] == params['admin_user']:
        return render_template('Add Post.html', params=params)
    if request.method == 'POST':
        log_db = mysql.connector.connect(
            host=params['host'],
            user=params['user'],
            password=params['password'],
            database=params['database']
        )
        log_cursor = log_db.cursor()
        if request.method == 'POST':
            log = request.form
            email = log['email']
            password = log['password']
            session['email'] = log['email']
            if email == params['admin_user'] and password == params['admin_pass']:
                s = session['email']
                return render_template('Add Post.html', name=s, params=params)
            else:
                log_cursor.execute(
                    "select * from signup where email = '" + email + "' and password = '" + password + "'")
                log_cursor.fetchall()
                count = log_cursor.rowcount
                if count == 1:
                    log_db.commit()
                    log_cursor.close()
                    s = session['email']
                    return render_template('Welcome.html', name=s, params=params)
                else:
                    return "Wrong credentials."
    return render_template('Login.html', params=params)


@app.route("/logout")
def logout():
    session.pop('email', None)
    return redirect('/login')


@app.route("/signup", methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        re_password = request.form.get('con_pass')
        if password == re_password:
            entry = Signup(name=name, email=email, password=password, con_pass=re_password)
            db.session.add(entry)
            db.session.commit()
            return "Registered Successfully"
        else:
            return "Your password don't match."
    return render_template('signup page.html')


@app.route("/contact", methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        '''Fetch data and add it to the database'''
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')
        entry = Contacts(name=name, email=email, subject=subject, message=message, date=datetime.now())
        db.session.add(entry)
        db.session.commit()
        mail.send_message("New message from " + name,
                          sender=email,
                          recipients=[params['mail_user']],
                          body=message)
    return render_template('contact.html', params=params)


@app.route("/add-post")
def add_post():
    return render_template('Add Post.html', params=params)


@app.route("/add-post/<string:sno>", methods=['GET', 'POST'])
def uploader(sno):
    if 'email' in session and session['email'] == params['admin_user']:
        if request.method == 'POST':
            title = request.form.get('title')
            content = request.form.get('content')
            file = request.form.get('file')
            # upload = request.files['upload']
            # storage.child("notice/new.pdf").put(upload)
            # file = storage.child('notice/new.pdf').get_url(None)
            category = request.form.get('category')
            date = datetime.now()

            if sno == '0':
                post = Posts(title=title, content=content, file=file, category=category, date=date)
                db.session.add(post)
                db.session.commit()

    post = Posts.query.filter_by(sno=sno).first()
    return render_template('Add Post.html', params=params, post=post, sno=sno)


@app.route("/add-user")
def add_user():
    return render_template('Add User.html', params=params)


@app.route("/manage-post")
def manage_post():
    posts = Posts.query.filter_by().all()
    last = math.ceil(len(posts) / int(params['no_of_posts']))
    page = request.args.get('page')
    if not str(page).isnumeric():
        page = 1
    page = int(page)
    posts = posts[(page - 1) * int(params['no_of_posts']):(page - 1) * int(params['no_of_posts']) + int(
        params['no_of_posts'])]
    if page == 1:
        prev = "#"
        nex = "/manage-post?page=" + str(page + 1)
    elif page == last:
        prev = "/manage-post?page=" + str(page - 1)
        nex = "#"
    else:
        prev = "/manage-post?page=" + str(page - 1)
        nex = "/manage-post?page=" + str(page + 1)
    return render_template('Manage Post.html', params=params, posts=posts, prev=prev, nex=nex)


@app.route("/edit/<string:sno>", methods=['GET', 'POST'])
def edit(sno):
    # global title, content, file, category, date
    if 'email' in session and session['email'] == params['admin_user']:
        if request.method == "POST":
            title = request.form.get('title')
            content = request.form.get('content')
            file = request.form.get('file')
            category = request.form.get('category')
            date = datetime.now()

            post = Posts.query.filter_by(sno=sno).first()
            post.title = title
            post.content = content
            post.file = file
            post.category = category
            post.date = date
            db.session.commit()
            return redirect('/edit/' + sno)

    post = Posts.query.filter_by(sno=sno).first()
    return render_template('edit.html', params=params, post=post, sno=sno)


@app.route("/manage-post/<string:post_sno>", methods=['GET'])
def post_route(post_sno):
    post = Posts.query.filter_by(sno=post_sno).first()
    return render_template('Manage Post.html', params=params, post=post)


@app.route("/manage-user")
def manage_user():
    return render_template('Manage User.html', params=params)


@app.route("/recent-post")
def recent_post():
    posts = Posts.query.filter_by().all()
    last = math.ceil(len(posts)/int(params['no_of_posts']))
    page = request.args.get('page')
    if not str(page).isnumeric():
        page = 1
    page = int(page)
    posts = posts[(page-1)*int(params['no_of_posts']):(page-1)*int(params['no_of_posts']) + int(params['no_of_posts'])]
    if page == 1:
        prev = "#"
        nex = "/recent-post?page=" + str(page+1)
    elif page == last:
        prev = "/recent-post?page=" + str(page-1)
        nex = "#"
    else:
        prev = "/recent-post?page=" + str(page - 1)
        nex = "/recent-post?page=" + str(page + 1)
    return render_template('Recent Posts.html', params=params, posts=posts, prev=prev, nex=nex)


@app.route("/post/<string:post_sno>", methods=['GET'])
def show_route(post_sno):
    post = Posts.query.filter_by(sno=post_sno).first()
    return render_template('post.html', params=params, post=post)


@app.route("/stud-posts")
def student_posts():
    posts = Posts.query.filter_by().all()
    last = math.ceil(len(posts) / int(params['no_of_posts']))
    page = request.args.get('page')
    if not str(page).isnumeric():
        page = 1
    page = int(page)
    posts = posts[(page - 1) * int(params['no_of_posts']):(page - 1) * int(params['no_of_posts']) + int(
        params['no_of_posts'])]
    if page == 1:
        prev = "#"
        nex = "/stud-posts?page=" + str(page + 1)
    elif page == last:
        prev = "/stud-posts?page=" + str(page - 1)
        nex = "#"
    else:
        prev = "/stud-posts?page=" + str(page - 1)
        nex = "/stud-posts?page=" + str(page + 1)
    return render_template('Students posts.html', params=params, posts=posts, prev=prev, nex=nex)


app.run(debug=True)
