from flask import Flask, render_template, request
import mysql.connector
from flask_mail import Mail
import json
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime


with open('config.json', 'r') as c:
    params = json.load(c)["params"]

local_server = True
app = Flask(__name__)
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


@app.route("/")
def hello():
    return render_template('index.html', params=params)


@app.route("/inner-pages")
def inside():
    return render_template('inner-page.html', params=params)


@app.route("/login", methods=['GET', 'POST'])
def login():
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
        log_cursor.execute("select * from signup where email = '" + email + "' and password = '" + password + "'")
        log_cursor.fetchall()
        count = log_cursor.rowcount
        if count == 1:
            log_db.commit()
            log_cursor.close()
            return render_template('inner-page.html', params=params)
        else:
            return "Wrong credentials."
    return render_template('Login.html')


@app.route("/signup", methods=['GET', 'POST'])
def signup():
    sign_db = mysql.connector.connect(
        host=params['host'],
        user=params['user'],
        password=params['password'],
        database=params['database']
    )
    sign_cursor = sign_db.cursor()
    if request.method == 'POST':
        sign = request.form
        name = sign['name']
        email = sign['email']
        password = sign['password']
        re_password = sign['con_pass']
        if password == re_password:
            sign_cursor.execute("insert into signup (name, email, password, con_pass) values(%s, %s, %s, %s)",
                                (name, email, password, re_password))
            sign_db.commit()
            sign_cursor.close()
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


app.run(debug=True)
