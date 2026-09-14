from flask import Flask, request, render_template_string, redirect, session, jsonify
import os

app = Flask(__name__)
app.secret_key = "citylords_secret_2024"

ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "admin123")

SUPABASE_URL = os.environ.get("SUPABASE_URL", "Not Set")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "Not Set")
supa_connected = "Yes" if SUPABASE_URL != "Not Set" else "No - Add in Render Env"

LOGIN_PAGE = """
<!DOCTYPE html>
<html><head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CityLords Login</title>
<style>
body{background:#0f0f0f;color:#fff;font-family:Arial;display:flex;justify-content:center;align-items:center;height:100vh;margin:0}
.box{background:#1c1c1c;padding:30px;border-radius:15px;width:90%;max-width:350px;text-align:center}
input{width:90%;padding:12px;margin:8px 0;border-radius:8px;border:none;background:#2a2a2a;color:#fff}
button{width:95%;padding:12px;background:#00ff88;color:#000;font-weight:bold;border:none;border-radius:8px;margin-top:10px}
</style>
</head>
<body>
<div class="box">
<h2 style="color:#00ff88">CityLords</h2>
<p>Admin Panel</p>
<form method="POST">
<input name="username" placeholder="Username" required>
<input name="password" type="password" placeholder="Password" required>
<button type="submit">Login</button>
</form>
<p style="color:#ff5555">MSG_PLACEHOLDER</p>
</div>
</body></html>
"""

DASHBOARD_PAGE = """
<!DOCTYPE html>
<html><head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Dashboard</title>
<style>
body{background:#0f0f0f;color:#fff;font-family:Arial;margin:0;padding:15px}
.header{display:flex;justify-content:space-between;align-items:center;background:#1c1c1c;padding:15px;border-radius:10px}
.card{background:#1c1c1c;padding:15px;margin:15px 0;border-radius:10px}
.btn{padding:8px 15px;border:none;border-radius:6px;font-weight:bold}
.btn-green{background:#00ff88;color:#000}
.btn-red{background:#ff4444;color:#fff}
</style>
</head>
<body>
<div class="header">
<h3>CityLords LIVE</h3>
<a href="/logout"><button class="btn btn-red">Logout</button></a>
</div>
<div class="card">
<h4>Status</h4>
<p>Flask: LIVE</p>
<p>Supabase: SUPA_STATUS</p>
<p>Link: https://citylordsbot-1.onrender.com</p>
</div>
<div class="card">
<h4>Ready!</h4>
<p>Your migration from Telegram to Web is successful!</p>
<p>Next step: I will add full task and group management after this deploys.</p>
</div>
</body></html>
"""

@app.route("/", methods=["GET","POST"])
def login():
    if session.get("logged_in"):
        return redirect("/dashboard")
    msg = ""
    if request.method == "POST":
        u = request.form.get("username")
        p = request.form.get("password")
        if u == ADMIN_USER and p == ADMIN_PASS:
            session["logged_in"] = True
            return redirect("/dashboard")
        else:
            msg = "Invalid login"
    page = LOGIN_PAGE.replace("MSG_PLACEHOLDER", msg)
    return render_template_string(page)

@app.route("/dashboard")
def dashboard():
    if not session.get("logged_in"):
        return redirect("/")
    page = DASHBOARD_PAGE.replace("SUPA_STATUS", supa_connected)
    return render_template_string(page)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/health")
def health():
    return jsonify({"status":"live"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
