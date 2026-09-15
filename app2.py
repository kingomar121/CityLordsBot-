from flask import Flask
app = Flask(__name__)
@app.route('/')
def home():
    return 'CityLords LIVE'
@app.route('/health')
def health():
    return 'OK'
