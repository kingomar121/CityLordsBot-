from flask import Flask, render_template_string
import os
from supabase import create_client

app = Flask(__name__)

# Get keys from Render Environment
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

HTML = """
<html>
<head><title>CityLords Dashboard</title></head>
<body style="font-family: Arial; padding: 20px;">
    <h1>👑 CityLords Dashboard Live!</h1>
    <p>Status: {{status}}</p>
    <p>Total Users: {{count}}</p>
    <h3>Last 5 Users:</h3>
    <ul>
    {% for u in users %}
        <li>{{u}}</li>
    {% endfor %}
    </ul>
    <br><br>
    <a href="/">Refresh</a>
</body>
</html>
"""

@app.route('/')
def home():
    status = "Connected to Supabase ✅" if supabase else "No Supabase Keys ❌"
    count = 0
    users = []
    if supabase:
        try:
            data = supabase.table("users").select("*").limit(5).execute()
            users = [str(x) for x in data.data]
            count_data = supabase.table("users").select("*", count="exact").execute()
            count = count_data.count if hasattr(count_data, 'count') else len(data.data)
        except Exception as e:
            status = f"Error: {e}"
    return render_template_string(HTML, status=status, count=count, users=users)

if __name__ == '__main__':
    app.run()
