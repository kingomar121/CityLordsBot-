from flask import Flask, render_template_string, request, redirect, session
import os

app = Flask(__name__)
app.secret_key = "citylords_secret"

HTML = """
<!DOCTYPE html>
<html>
<head><title>CityLords</title></head>
<body style="background:#111;color:white;text-align:center;padding:50px;font-family:Arial">
<h1>CityLords Admin Panel is LIVE ✅</h1>
<p>Your deploy works!</p>
<form method="POST">
<input name="user" placeholder="Username" style="padding:10px"><br><br>
<input name="pass" type="password" placeholder="Password" style="padding:10px"><br><br>
<button style="padding:10px 20px">Login</button>
</form>
<p>{{msg}}</p>
</body>
</html>
"""

@app.route("/", methods=["GET","POST"])
def home():
    msg=""
    if request.method=="POST":
        if request.form.get("user")=="admin" and request.form.get("pass")=="admin123":
            return "<h1>Welcome Admin! Dashboard coming next.</h1><p><a href='/'>Logout</a></p>"
        else:
            msg="Wrong password"
    return render_template_string(HTML, msg=msg)

if __name__ == "__main__":
    app.run()
