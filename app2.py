from flask import Flask, request, redirect, session, jsonify
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'citylords-2024-secret-key-xyz'

# In-memory storage
users_db = {}
payments_db = []
ADMIN_CODE = 'CITYADMIN2024'

@app.route('/')
def home():
    if 'user' in session:
        return redirect('/dashboard')
    return '''
    <html><head><title>CityLords</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
    body{font-family:Arial;background:#0f172a;color:white;margin:0;padding:20px;text-align:center}
   .box{max-width:400px;margin:50px auto;background:#1e293b;padding:30px;border-radius:15px}
    input{width:100%;padding:12px;margin:10px 0;border-radius:8px;border:none;box-sizing:border-box}
    button{width:100%;padding:12px;background:#3b82f6;color:white;border:none;border-radius:8px;font-weight:bold;cursor:pointer}
    a{color:#60a5fa}
    </style></head><body>
    <div class="box">
    <h1>🏙️ CityLords</h1>
    <p>Real Estate Investment Platform</p>
    <h3>Login / Register</h3>
    <form action="/login" method="post">
    <input name="username" placeholder="Username" required>
    <input name="password" type="password" placeholder="Password" required>
    <button type="submit">Enter Dashboard</button>
    </form>
    <p style="font-size:12px;margin-top:20px">Admin? Use code CITYADMIN2024 as username</p>
    </div></body></html>
    '''

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username','').strip()
    password = request.form.get('password','').strip()
    if not username:
        return redirect('/')
    if username == ADMIN_CODE:
        session['user'] = 'ADMIN'
        session['is_admin'] = True
        return redirect('/admin')
    if username not in users_db:
        users_db[username] = {'password':password,'balance':0,'joined':datetime.now().strftime('%Y-%m-%d')}
    session['user'] = username
    session['is_admin'] = False
    return redirect('/dashboard')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/')
    user = session['user']
    if session.get('is_admin'):
        return redirect('/admin')
    info = users_db.get(user, {'balance':0})
    return f'''
    <html><head><title>Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
    body{{font-family:Arial;background:#0f172a;color:white;margin:0;padding:15px}}
   .card{{background:#1e293b;padding:20px;border-radius:12px;margin:10px 0}}
    button{{padding:10px 15px;background:#3b82f6;color:white;border:none;border-radius:8px;cursor:pointer;margin:5px}}
   .green{{background:#10b981}}.red{{background:#ef4444}}
    </style></head><body>
    <h2>Welcome, {user} 👋</h2>
    <div class="card"><h3>Balance: ${info.get('balance',0)}</h3><p>Member since: {info.get('joined','Today')}</p></div>
    <div class="card"><h3>🏘️ Investment Plans</h3><p>Starter: $100 -> $150 in 30 days</p><p>Pro: $500 -> $800 in 30 days</p><button onclick="invest(100)">Invest $100</button><button onclick="invest(500)">Invest $500</button></div>
    <div class="card"><a href="/logout"><button class="red">Logout</button></a> <a href="/"><button>Home</button></a></div>
    <script>
    function invest(amt){{ fetch('/api/invest',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{amount:amt}})}}).then(r=>r.json()).then(d=>{{alert(d.message); location.reload()}}) }}
    </script>
    </body></html>
    '''

@app.route('/admin')
def admin():
    if not session.get('is_admin'):
        return 'Access Denied - Admin Only'
    total_users = len(users_db)
    total_pay = sum(p['amount'] for p in payments_db)
    users_list = ''.join([f"<tr><td>{u}</td><td>${d['balance']}</td><td>{d['joined']}</td></tr>" for u,d in users_db.items()])
    pays_list = ''.join([f"<tr><td>{p['user']}</td><td>${p['amount']}</td><td>{p['date']}</td></tr>" for p in payments_db[-20:]])
    return f'''
    <html><head><title>Admin</title><meta name="viewport" content="width=device-width, initial-scale=1">
    <style>body{{font-family:Arial;background:#0f172a;color:white;padding:15px}} table{{width:100%;background:#1e293b;border-radius:8px}} td,th{{padding:8px;text-align:left}}.card{{background:#1e293b;padding:15px;border-radius:10px;margin:10px 0}}</style>
    </head><body>
    <h1>Admin Dashboard 👑</h1>
    <div class="card">Total Users: {total_users} | Total Investments: ${total_pay}</div>
    <div class="card"><h3>Users</h3><table><tr><th>User</th><th>Balance</th><th>Joined</th></tr>{users_list}</table></div>
    <div class="card"><h3>Recent Payments</h3><table><tr><th>User</th><th>Amount</th><th>Date</th></tr>{pays_list}</table></div>
    <a href="/logout"><button style="padding:10px;background:#ef4444;color:white;border:none;border-radius:8px">Logout</button></a>
    </body></html>
    '''

@app.route('/api/invest', methods=['POST'])
def api_invest():
    if 'user' not in session:
        return jsonify({'message':'Not logged in'})
    data = request.get_json()
    amt = data.get('amount',0)
    user = session['user']
    users_db[user]['balance'] += amt
    payments_db.append({'user':user,'amount':amt,'date':datetime.now().strftime('%Y-%m-%d %H:%M')})
    return jsonify({'message':f'Success! Invested ${amt}. Balance updated.'})

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/health')
def health():
    return 'OK'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
