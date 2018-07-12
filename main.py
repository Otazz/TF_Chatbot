from flask import Flask, request, render_template
import db_utils
import chat

app = Flask(__name__)

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/msg')
def response():
	text = request.args.get("text")
	response = chat.predict(text)
	saver = {
		"input": text,
		"output": response
	}
	db_utils.save_input(saver)
	return response

if __name__ == "__main__":
	app.run(host='0.0.0.0')