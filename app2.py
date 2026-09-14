import os, re, secrets, requests
from datetime import datetime, date, timezone, timedelta
from flask import Flask, request, jsonify, render_template_string
from supabase import create_client

app = Flask(__name__)

SUPABASE_URL=os.getenv("SUPABASE_URL")
SUPABASE_KEY=os.getenv("SUPABASE_KEY")
PAYSTACK_SECRET=os.getenv("PAYSTACK_SECRET")
PAYSTACK_PUBLIC=os.getenv("PAYSTACK_PUBLIC", "pk_live_YOUR_PUBLIC_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

def slugify(n):
    if not n: return f"shop-{secrets.token_hex(2)}"
    s=re.sub(r'[^a-z0-9]+','-',n.lower()).strip('-')
    return s[:40] if s and len(s)>=2 else f"shop-{secrets.token_hex(2)}"
def safe_parse(s):
    if not s: return None
    try: return datetime.fromisoformat(str(s).replace('Z','+00:00'))
    except: return None

REGISTER_HTML = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{font-family:Arial;padding:20px;background:#f5f5f5}.box{background:white;padding:25px;border-radius:12px;max-width:450px;margin:auto;box-shadow:0 2px 10px rgba(0,0,0,0.1)} input,select{width:100%;padding:12px;margin:8px 0 15px;border:1px solid #ddd;border-radius:8px;box-sizing:border-box} button{background:#25D366;color:white;padding:12px;width:100%;border:none;border-radius:8px;font-weight:bold;cursor:pointer} label{font-size:13px;font-weight:bold}</style>
</head><body><div class="box">
<h2>CityLords - Register VENDOR (FREE)</h2>
<p>FREE = 10 CUSTOMER visits/day<br>PAID = Unlimited (auto when you pay ₦2000)</p>
<form method="POST">
<label>Business Name (VENDOR)</label><input name="business_name" required maxlength="60" placeholder="Mama Gold Kitchen">
<label>WhatsApp (VENDOR)</label><input name="whatsapp" required placeholder="08012345678">
<label>Category</label><select name="category" required><option value="">Select...</option><option>Fashion</option><option>Real Estate</option><option>Eatery</option><option>Electronics</option><option>Gas / Energy</option><option>Beauty</option><option>Others</option></select>
<hr><p><b>FAQs - CUSTOMERS will see these inside 3-dot menu (FAQ from VENDOR)</b></p>
<label>FAQ 1 - How to order?</label><input name="faq1" placeholder="Chat product name, we reply fast" maxlength="200">
<label>FAQ 2 - Delivery?</label><input name="faq2" placeholder="We deliver Kano & nationwide" maxlength="200">
<label>FAQ 3 - Payment?</label><input name="faq3" placeholder="Pay on delivery or transfer" maxlength="200">
<button type="submit">Create FREE Link</button>
</form></div></body></html>
"""

SUCCESS_HTML = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{font-family:Arial;padding:20px;background:#f5f5f5;text-align:center}.box{background:white;padding:25px;border-radius:12px;max-width:400px;margin:30px auto}.link{background:#e8f5e9;padding:12px;border-radius:8px;word-break:break-all;margin:15px 0;border:1px dashed #25D366} button{background:#25D366;color:white;padding:10px 20px;border:none;border-radius:8px;cursor:pointer}</style>
</head><body><div class="box">
<h2>🎉 VENDOR Registered!</h2><p>CUSTOMERS will chat via this link:</p><div class="link">{{link}}</div>
<button onclick="navigator.clipboard.writeText('{{link}}');alert('Copied!')">COPY LINK</button><br><br>
<a href="/upgrade/{{handle}}"><button style="background:#1e88e5">Upgrade to Unlimited - Auto (₦2000)</button></a>
</div></body></html>
"""

CHAT_HTML = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body{margin:0;font-family:Arial;background:#e5ddd5;display:flex;flex-direction:column;height:100vh}
.header{background:#075E54;color:white;padding:12px 15px;display:flex;justify-content:space-between;align-items:center}
.menu{position:relative}.dots{font-size:26px;cursor:pointer;padding:5px 12px}
.dropdown{display:none;position:absolute;right:0;top:40px;background:white;color:black;border-radius:10px;box-shadow:0 4px 15px rgba(0,0,0,0.25);width:240px;z-index:100;overflow:hidden}
.dropdown div{padding:14px 16px;cursor:pointer;border-bottom:1px solid #f0f0f0;font-size:14px}
.dropdown div:hover{background:#f5f5f5}
.chat-area{flex:1;overflow-y:auto;padding:15px;display:flex;flex-direction:column;gap:10px}
.bubble{max-width:78%;padding:11px 14px;border-radius:12px;font-size:14.5px;line-height:1.4;box-shadow:0 1px 1px rgba(0,0,0,0.08)}
.bot{background:white;align-self:flex-start;border-bottom-left-radius:3px}
.user{background:#dcf8c6;align-self:flex-end;border-bottom-right-radius:3px}
.input-area{background:#f0f0f0;padding:10px;display:flex;gap:10px;align-items:center}
.input-area input{flex:1;padding:12px 16px;border:none;border-radius:25px;outline:none}
.input-area button{background:#25D366;border:none;color:white;width:48px;height:48px;border-radius:50%;font-size:22px;cursor:pointer}
.modal{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);z-index:300;justify-content:center;align-items:center}
.modal-box{background:white;padding:22px;border-radius:14px;max-width:360px;width:90%;max-height:80vh;overflow-y:auto}
.close{float:right;cursor:pointer;font-size:22px}
</style>
</head><body>
<div class="header">
<div><b>{{biz}}</b><br><small>{{cat}} • Online 24/7</small></div>
<div class="menu"><div class="dots" onclick="toggleMenu()">⋮</div>
<div class="dropdown" id="dd">
<div onclick="openModal('ratingModal')">⭐ Rating & Reviews</div>
<div onclick="openModal('faqModal')">❓ FAQ</div>
<div onclick="openModal('reportModal')">🚩 Report Vendor</div>
<div onclick="openModal('supportModal')">📞 Contact Support</div>
</div></div>
</div>

<div class="chat-area" id="chat">
<div class="bubble bot">Hi CUSTOMER! 👋 Welcome to {{biz}}. I'm {{biz}} bot - replying 24/7.<br><br>What product did you see on TikTok? Type your message below 👇</div>
</div>

<div class="input-area">
<input id="msg" placeholder="Type a message..." onkeypress="if(event.key==='Enter')send()">
<button onclick="send()">➤</button>
</div>

<!-- 3-DOT MENU CONTENT - CORRECT AS YOU SAID -->
<div class="modal" id="ratingModal"><div class="modal-box"><span class="close" onclick="closeModals()">✕</span>
<h3>⭐ Rating - {{biz}}</h3><p style="font-size:48px;text-align:center;color:#FFC107">{{rating}} ★</p>
<p style="text-align:center">Based on {{reviews}} CUSTOMER reviews<br><br>Trusted VENDOR verified by ADMIN (CityLords)</p>
</div></div>

<div class="modal" id="faqModal"><div class="modal-box"><span class="close" onclick="closeModals()">✕</span>
<h3>❓ FAQ - From VENDOR ({{biz}})</h3>
<p><b>Q: How to order?</b><br>A: {{faq1}}</p>
<p><b>Q: Delivery?</b><br>A: {{faq2}}</p>
<p><b>Q: Payment?</b><br>A: {{faq3}}</p>
<small>FAQs submitted by VENDOR owner</small>
</div></div>

<div class="modal" id="reportModal"><div class="modal-box"><span class="close" onclick="closeModals()">✕</span>
<h3>🚩 Report VENDOR</h3><p>Report {{biz}} to ADMIN (CityLords) if scam:</p>
<button onclick="reportVendor()" style="background:#e53935;color:white;padding:12px;border:none;border-radius:8px;width:100%">Report {{biz}}</button>
</div></div>

<div class="modal" id="supportModal"><div class="modal-box"><span class="close" onclick="closeModals()">✕</span>
<h3>📞 Contact Support</h3><p><b>ADMIN (CityLords):</b><br>Email: support@citylords.com<br>For CUSTOMERS: If VENDOR not responding<br>For VENDORS: Upgrade help</p>
</div></div>

<script>
function toggleMenu(){var m=document.getElementById('dd');m.style.display=m.style.display==='block'?'none':'block'}
window.onclick=function(e){ if(!e.target.closest('.menu')&&!e.target.closest('.modal-box')){ document.getElementById('dd').style.display='none'; if(e.target.classList.contains('modal')) closeModals(); } }
function closeModals(){ document.querySelectorAll('.modal').forEach(m=>m.style.display='none'); document.getElementById('dd').style.display='none'; }
function openModal(id){ document.getElementById(id).style.display='flex'; document.getElementById('dd').style.display='none'; }
function reportVendor(){ fetch('/report/{{handle}}',{method:'POST'}).then(()=>{ alert('Reported to ADMIN'); closeModals(); }) }
function send(){
  var i=document.getElementById('msg'); var t=i.value.trim(); if(!t) return;
  var c=document.getElementById('chat'); var u=document.createElement('div'); u.className='bubble user'; u.textContent=t; c.appendChild(u);
  i.value=''; c.scrollTop=c.scrollHeight;
  setTimeout(()=>{ var b=document.createElement('div'); b.className='bubble bot'; b.textContent='Received! VENDOR {{biz}} will reply on WhatsApp soon. You said: '+t; c.appendChild(b); c.scrollTop=c.scrollHeight; },700);
}
</script>
</body></html>
"""

LIMIT_HTML = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><script src="https://js.paystack.co/v1/inline.js"></script>
<style>body{font-family:Arial;text-align:center;padding:20px;background:#fff8f0}.box{max-width:400px;margin:40px auto;background:white;padding:25px;border-radius:14px;box-shadow:0 2px 12px rgba(0,0,0,0.1)}</style>
</head><body><div class="box">
<h2>⏰ FREE Limit Reached</h2><p><b>{{biz}}</b> FREE VENDORS get 10 CUSTOMER visits/day.<br>Limit reached.</p>
<p><b>VENDOR:</b> Pay ₦2000 for unlimited CUSTOMERS + chats - Auto activates!</p>
<button onclick="pay()" style="background:#1e88e5;color:white;padding:14px 30px;border:none;border-radius:10px;font-size:16px">Pay ₦2000 - Auto Upgrade</button>
<p style="font-size:11px;color:gray;margin-top:15px">Automatic - ADMIN (CityLords) does nothing - Built $0 cost</p>
<script>
function pay(){
  var h=PaystackPop.setup({
    key:'{{pubkey}}', email:'{{handle}}@citylords.com', amount:200000, currency:'NGN',
    ref:'CITY-'+Date.now()+'-{{handle}}',
    callback:function(r){ fetch('/verify/'+r.reference).then(x=>x.json()).then(d=>{ if(d.ok){ alert('SUCCESS! Auto-upgraded to unlimited!'); window.location='/c/{{handle}}'; } else alert('Failed'); }) },
    onClose:function(){}
  }); h.openIframe();
}
</script>
</div></body></html>
"""

ADMIN_HTML = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{font-family:Arial;padding:12px;background:#f5f5f5} table{width:100%;background:white;border-radius:8px;border-collapse:collapse} th,td{padding:8px;border-bottom:1px solid #eee;font-size:11px}.btn{padding:5px 8px;border:none;border-radius:5px;color:white;cursor:pointer;font-size:10px}.del{background:#e53935}.sus{background:#ff9800}.uns{background:#43a047}</style>
</head><body>
<h2>CityLords ADMIN - $0 Build - Auto Subscription System</h2>
<p>ADMIN=CityLords | VENDORS=Sellers | CUSTOMERS=Buyers | VENDOR upgrade is AUTOMATIC, ADMIN does NOT activate</p>
<a href="/register"><button>+ Add VENDOR</button></a><br><br>
<table><tr><th>VENDOR</th><th>Link /c/</th><th>Plan</th><th>Visits</th><th>Expiry</th><th>ADMIN (Scam only)</th></tr>
{% for v in vendors %}
<tr><td>{{v.business_name}}<br><small>{{v.category}} ⭐{{v.rating or 5}}</small></td><td>/c/{{v.handle}}</td><td><b style="color:{{'green' if v.plan=='paid' else 'gray'}}">{{v.plan}}</b></td><td>{{v.daily_visits or 0}} {% if v.plan=='free' %}/10{% else %}/∞{% endif %}</td><td>{{v.subscription_end[:10] if v.subscription_end else '-'}}</td>
<td>
{% if v.status=='active' %}<button class="btn sus" onclick="fetch('/admin/suspend/{{v.handle}}',{method:'POST'}).then(()=>location.reload())">Suspend Scam</button>{% else %}<button class="btn uns" onclick="fetch('/admin/unsuspend/{{v.handle}}',{method:'POST'}).then(()=>location.reload())">Unsuspend</button>{% endif %}
<button class="btn del" onclick="if(confirm('Delete?'))fetch('/admin/delete/{{v.handle}}',{method:'POST'}).then(()=>location.reload())">Delete</button>
</td></tr>
{% endfor %}
</table></body></html>
"""

@app.route('/register', methods=['GET','POST'])
def register():
    if not supabase: return "Config error",500
    if request.method=='GET': return REGISTER_HTML
    biz=request.form.get('business_name','').strip()[:60]
    wa=re.sub(r'[^0-9+]','',request.form.get('whatsapp','').strip())[:15]
    cat=request.form.get('category','Others')
    faq1=request.form.get('faq1','Chat here, VENDOR replies on WhatsApp')[:200]
    faq2=request.form.get('faq2','We deliver Kano & nationwide')[:200]
    faq3=request.form.get('faq3','Pay on delivery or transfer')[:200]
    if len(biz)<2 or len(wa)<10: return "Invalid VENDOR data",400
    base=slugify(biz); handle=base; c=1
    while True:
        ex=supabase.table('vendors').select('handle').eq('handle',handle).execute()
        if not ex.data: break
        c+=1; handle=f"{base}-{c}"
        if c>100: handle=f"{base}-{secrets.token_hex(2)}"; break
    supabase.table('vendors').insert({"business_name":biz,"handle":handle,"whatsapp":wa,"category":cat,"faq1":faq1,"faq2":faq2,"faq3":faq3,"plan":"free","status":"active","daily_visits":0,"last_visit_date":str(date.today()),"rating":5.0,"total_reviews":0,"subscription_end":None}).execute()
    return render_template_string(SUCCESS_HTML, link=f"https://citylordsbot-1.onrender.com/c/{handle}", handle=handle)

@app.route('/c/<handle>')
def vendor_chat(handle):
    if not supabase: return "Config error",500
    handle=re.sub(r'[^a-z0-9\-]','',handle.lower())[:60]
    res=supabase.table('vendors').select('*').eq('handle',handle).execute()
    if not res.data: return "VENDOR not found",404
    v=res.data[0]
    if v.get('status')=='suspended': return f"<h2 style='text-align:center;margin-top:50px'>🚫 {v.get('business_name')} suspended by ADMIN for reports.</h2>"
    if v.get('plan')=='paid' and v.get('subscription_end'):
        exp=safe_parse(v['subscription_end'])
        if exp and exp < datetime.now(timezone.utc):
            supabase.table('vendors').update({"plan":"free","subscription_end":None}).eq('handle',handle).execute()
            v['plan']='free'
    today=str(date.today()); daily=v.get('daily_visits') or 0
    if v.get('last_visit_date')!=today:
        supabase.table('vendors').update({"daily_visits":0,"last_visit_date":today}).eq('handle',handle).execute()
        daily=0
    if v.get('plan')=='free' and daily>=10:
        return render_template_string(LIMIT_HTML, biz=v.get('business_name'), handle=handle, pubkey=PAYSTACK_PUBLIC)
    supabase.table('vendors').update({"daily_visits":daily+1}).eq('handle',handle).execute()
    return render_template_string(CHAT_HTML, biz=v.get('business_name','Shop'), cat=v.get('category','Others'), rating=v.get('rating') or 5.0, reviews=v.get('total_reviews') or 0, handle=handle, faq1=v.get('faq1') or "Chat here, VENDOR replies fast", faq2=v.get('faq2') or "We deliver Kano & nationwide", faq3=v.get('faq3') or "Pay on delivery")

@app.route('/upgrade/<handle>')
def upgrade(handle):
    handle=re.sub(r'[^a-z0-9\-]','',handle.lower())[:60]
    res=supabase.table('vendors').select('business_name').eq('handle',handle).execute()
    biz=res.data[0]['business_name'] if res.data else handle
    return render_template_string(LIMIT_HTML, biz=biz, handle=handle, pubkey=PAYSTACK_PUBLIC)

@app.route('/verify/<ref>')
def verify(ref):
    if not PAYSTACK_SECRET: return jsonify(ok=False, error="Paystack secret not set")
    try:
        parts=ref.split('-'); handle='-'.join(parts[2:]) if len(parts)>=3 else ref
        handle=re.sub(r'[^a-z0-9\-]','',handle.lower())[:60]
        r=requests.get(f'https://api.paystack.co/transaction/verify/{ref}', headers={'Authorization': f'Bearer {PAYSTACK_SECRET}'}, timeout=10)
        data=r.json()
        if r.status_code==200 and data.get('data',{}).get('status')=='success':
            v=supabase.table('vendors').select('subscription_end').eq('handle',handle).execute()
            curr=safe_parse(v.data[0].get('subscription_end')) if v.data else None
            if curr and curr > datetime.now(timezone.utc):
                new_exp = curr + timedelta(days=30)
            else:
                new_exp = datetime.now(timezone.utc) + timedelta(days=30)
            supabase.table('vendors').update({"plan":"paid","subscription_end":new_exp.isoformat(),"daily_visits":0}).eq('handle',handle).execute()
            return jsonify(ok=True)
    except Exception as e:
        return jsonify(ok=False, error=str(e))
    return jsonify(ok=False)

@app.route('/admin')
def admin():
    vendors=supabase.table('vendors').select('*').order('created_at',desc=True).limit(300).execute()
    return render_template_string(ADMIN_HTML, vendors=vendors.data or [])

@app.route('/admin/delete/<handle>', methods=['POST'])
def del_v(handle): supabase.table('vendors').delete().eq('handle',handle).execute(); return jsonify(ok=True)
@app.route('/admin/suspend/<handle>', methods=['POST'])
def sus(handle): supabase.table('vendors').update({"status":"suspended"}).eq('handle',handle).execute(); return jsonify(ok=True)
@app.route('/admin/unsuspend/<handle>', methods=['POST'])
def uns(handle): supabase.table('vendors').update({"status":"active"}).eq('handle',handle).execute(); return jsonify(ok=True)
@app.route('/report/<handle>', methods=['POST'])
def rep(handle):
    try: supabase.table('reports').insert({"handle":handle,"created_at":datetime.now(timezone.utc).isoformat()}).execute()
    except: pass
    return jsonify(ok=True)

if __name__=='__main__': app.run(host='0.0.0.0',port=10000)
