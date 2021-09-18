from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def hello():
	return render_template('index.html')


@app.route("/inner-pages")
def inside():
	return render_template('inner-page.html')


app.run(debug=True)
