from flask import Flask
app = Flask(__name__)

@app.route("/")
def home():
    return "<h1>CityLords is LIVE ✅</h1><p>Test successful - Flask works!</p><p>Next: add login</p>"

@app.route("/health")
def health():
    return "OK"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
