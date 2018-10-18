from flask import Flask, request, render_template
import db_utils
import chat

APP = Flask(__name__)
#DBB = db_utils.DB()
S2S = chat.Seq2Seq()

@APP.route('/')
def index():
  return render_template('index.html')

@APP.route('/train')
def train():
  return S2S.train()

@APP.route('/msg')
def response():
  text = request.args.get("text")
  response_out = S2S.predict(text)
  saver = {
    "input": text,
    "output": response_out
  }
  #DBB.save_input(saver)
  return response_out

if __name__ == "__main__":
  APP.run(host='0.0.0.0')