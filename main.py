from flask import Flask, render_template, request, session, redirect
import mysql.connector
from werkzeug.utils import secure_filename
from flask_mail import Mail
import json
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os


with open('config.json', 'r') as c:
    params = json.load(c)["params"]

local_server = True
app = Flask(__name__)
app.secret_key = 'super-secret-key'
app.config['UPLOAD_FOLDER'] = params['upload_location']
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

db = SQLAlchemy(app)


class Contacts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(25), nullable=False)
    subject = db.Column(db.String(30), nullable=False)
    message = db.Column(db.String(120), nullable=True)
    date = db.Column(db.String(12), nullable=True)


class Signup(db.Model):
    name = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(30), nullable=False, primary_key=True)
    password = db.Column(db.String(25), nullable=False)
    con_pass = db.Column(db.String(25), nullable=False)


class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=True)
    slug = db.Column(db.String(25), nullable=False)
    content = db.Column(db.String(120), nullable=True)
    file = db.Column(db.BLOB, nullable=False)
    date = db.Column(db.String(12), nullable=True)


@app.route("/")
def hello():
    return render_template('index.html', params=params)


@app.route("/inner-pages")
def inside():
    return render_template('inner-page.html', params=params)


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
                log_cursor.execute("select * from signup where email = '" + email + "' and password = '" + password + "'")
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


@app.route("/uploader", methods=['GET', 'POST'])
def uploader():
    if request.method == 'POST':
        f = request.files['file1']
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
        return "Uploaded Successfully"


@app.route("/add-user")
def add_user():
    return render_template('Add User.html', params=params)


@app.route("/manage-post")
def manage_post():
    return render_template('Manage Post.html', params=params)


@app.route("/manage-post/<string:post_slug>", methods=['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template('Manage Post.html', params=params, post=post)


@app.route("/manage-user")
def manage_user():
    return render_template('Manage User.html', params=params)


@app.route("/recent-post")
def recent_post():
    return render_template('Recent Posts.html', params=params)


app.run(debug=True)
