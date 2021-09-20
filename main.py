from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pymysql


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/tpo_site'
db = SQLAlchemy(app)
pymysql.install_as_MySQLdb()


class Contacts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(25), nullable=False)
    subject = db.Column(db.String(30), nullable=False)
    message = db.Column(db.String(120), nullable=True)
    date = db.Column(db.String(12), nullable=True)


@app.route("/")
def hello():
    return render_template('index.html')


@app.route("/inner-pages")
def inside():
    return render_template('inner-page.html')


@app.route("/login")
def login():
    return render_template('Login.html')


@app.route("/signup")
def signup():
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
    return render_template('contact.html')


app.run(debug=True)
