from flask import Flask, request, render_template_string, redirect, session, jsonify
import os
from supabase import create_client

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "citylords_secret_2024")

# Supabase Config
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "admin123")

LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CityLords Login</title>
<style>
body{background:#0f0f0f;color:#fff;font-family:Arial;display:flex;justify-content:center;align-items:center;height:100vh;margin:0}
.box{background:#1c1c1c;padding:30px;border-radius:15px;width:90%;max-width:350px;text-align:center;box-shadow:0 0 20px #000}
input{width:90%;padding:12px;margin:8px 0;border-radius:8px;border:none;background:#2a2a2a;color:#fff}
button{width:95%;padding:12px;background:#00ff88;color:#000;font-weight:bold;border:none;border-radius:8px;margin-top:10px;cursor:pointer}
h2{color:#00ff88}
</style>
</head>
<body>
<div class="box">
<h2>CityLords</h2>
<p>Admin Panel</p>
<form method="POST">
<input name="username" placeholder="Username" required>
<input name="password" type="password" placeholder="Password" required>
<button type="submit">Login</button>
</form>
<p style="color:#ff5555">{{msg}}</p>
</div>
</body>
</html>
"""

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CityLords Dashboard</title>
<style>
body{background:#0f0f0f;color:#fff;font-family:Arial;margin:0;padding:15px}
.header{display:flex;justify-content:space-between;align-items:center;background:#1c1c1c;padding:15px;border-radius:10px}
.card{background:#1c1c1c;padding:15px;margin:15px 0;border-radius:10px}
.btn{padding:8px 15px;border:none
