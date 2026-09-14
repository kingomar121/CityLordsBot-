import os
import asyncio
import threading
import uuid
from flask import Flask, request, jsonify, render_template_string
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from supabase import create_client, Client
from datetime import datetime

# --- Config ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
ADMIN_ID_STR = os.getenv("ADMIN_ID", "0")

try:
    ADMIN_ID = int(ADMIN_ID_STR)
except:
    ADMIN_ID = 0

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None
app = Flask(__name__)

# --- In-Memory Chat State for 24/7 Handler ---
# customer_id -> {stage, product, location, phone, vendor_slug}
chat_sessions = {}

CHAT_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{shop_name}} - Chat 24/7</title>
<style>
body{font-family:sans-serif;background:#f5f5f5;margin:0}
#box{max-width:480px;margin:auto;background:white;height:100vh;display:flex;flex-direction:column}
#head{background:#000;color:#fff;padding:15px;text-align:center;font-weight:bold}
#msgs{flex:1;overflow-y:auto;padding:15px}
.b{padding:10px 14px;border-radius:15px;margin:6px 0;max-width:80%;}
.user{background:#dcf8c6;margin-left:auto}
.bot{background:#eee}
#input{display:flex;padding:10px;border-top:1px solid #ddd}
#input input{flex:1;padding:12px;border:1px solid #ccc;border-radius:20px}
#input button{margin-left:8px;padding:12px 18px;border:none;background:#000;color:#fff;border-radius:20px}
small{color:gray}
</style>
</head>
<body>
<div id="box">
<div id="head">💬 {{shop_name}} - We Reply Instantly 24/7 <br><small>{{location}}</small></div>
<div id="msgs"></div>
<div id="input"><input id="txt" placeholder="Type which product you saw on TikTok..."><button onclick="send()">Send</button></div>
</div>
<script>
let cid = localStorage.getItem('cl_cid') || 'cust_'+Math.random().toString(36).substring(2,9);
localStorage.setItem('cl_cid', cid);
let vendor_slug = "{{slug}}";
function addMsg(t,who){
 let d=document.createElement('div'); d.className='b '+who; d.innerText=t;
 document.getElementById('msgs').appendChild(d);
 document.getElementById('msgs').scrollTop=99999;
}
addMsg("Hi! 👋 Welcome to {{shop_name}}. I reply instantly 24/7.\\nYou came from TikTok/FB. Which product did you see there? Please describe it (e.g 'LG microwave from last video')", "bot");
async function send(){
 let m=document.getElementById('txt').value; if(!m)return;
 addMsg(m,"user"); document.getElementById('txt').value="";
 let res=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({vendor_slug:vendor_slug,customer_id:cid,message:m})});
 let data=await res.json();
 addMsg(data.reply,"bot");
 if(data.done){ document.getElementById('input').innerHTML="<p style='text-align:center;padding:15px'>✅ Order received! Vendor will contact you shortly on WhatsApp.</p>"; }
}
document.getElementById('txt').addEventListener('keypress',function(e){if(e.key==='Enter')send()});
</script>
</body>
</html>
"""

# --- Helper: Get Vendor ---
def get_vendor_by_slug(slug):
    if not supabase: return None
    try:
        # try slug column first, then name
        res = supabase.table("vendors").select("*").ilike("name", slug.replace('-',' ')).execute()
        if res.data: return res.data[0]
        # if you have slug column
        try:
            res2 = supabase.table("vendors").select("*").eq("slug", slug).execute()
            if res2.data: return res2.data[0]
        except: pass
    except Exception as e:
        print(f"vendor lookup error: {e}")
    return {"name": slug.replace('-',' ').title(), "location": "PH City", "phone": "Vendor", "slug": slug}

def save_chat_order(vendor, session):
    if not supabase: return
    try:
        supabase.table("orders_chat").insert({
            "vendor_name": vendor.get('name'),
            "vendor_phone": vendor.get('phone'),
            "product_desc": session.get('product',''),
            "customer_location": session.get('location',''),
            "customer_phone": session.get('phone',''),
            "payment_method": session.get('payment',''),
            "customer_id": session.get('customer_id',''),
            "created_at": datetime.utcnow().isoformat()
        }).execute()
        print("Order saved")
    except Exception as e:
        print(f"Could not save to orders_chat (create table): {e}")

# --- 24/7 Chat API ---
@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.json
    slug = data.get("vendor_slug","").strip()
    cid = data.get("customer_id","anon")
    msg = data.get("message","").strip()

    vendor = get_vendor_by_slug(slug)
    key = f"{slug}_{cid}"
    sess = chat_sessions.get(key, {"stage":0,"customer_id":cid})

    stage = sess.get("stage",0)
    reply = ""
    done = False

    if stage == 0:
        sess["product"] = msg
        sess["stage"] = 1
        reply = f"Got it! '{msg}' ✅\n\nStill available. Where is your delivery location in {vendor.get('location','PH')}? (e.g. Rumuokoro, Garrison)"
    elif stage == 1:
        sess["location"] = msg
        sess["stage"] = 2
        reply = "Thanks! What is your phone number / WhatsApp number so vendor can reach you?"
    elif stage == 2:
        sess["phone"] = msg
        sess["stage"] = 3
        reply = "Perfect. How do you want to pay?\n1. Transfer Before Delivery\n2. Pay On Delivery (POD)\n\nReply 1 or 2"
    elif stage == 3:
        pay = "Transfer" if "1" in msg or "transfer" in msg.lower() else "Pay On Delivery"
        sess["payment"] = pay
        sess["stage"] = 4
        reply = f"Awesome!\n\nConfirming your order:\n• Product: {sess.get('product')}\n• Location: {sess.get('location')}\n• Phone: {sess.get('phone')}\n• Payment: {pay}\n• Shop: {vendor.get('name')}\n\nIs this correct? Reply YES to confirm."
    elif stage == 4:
        if "yes" in msg.lower() or "correct" in msg.lower() or "ok" in msg.lower():
            save_chat_order(vendor, sess)
            reply = f"✅ Order Confirmed! Thank you.\n\n{vendor.get('name')} will contact you shortly on {sess.get('phone')}.\n\nYour order number: {str(uuid.uuid4())[:8].upper()}\nWe reply 24/7 - no more DM ignored!"
            done = True
            sess["stage"] = 5
        else:
            reply = "No problem. Tell me what to correct? (Product, Location, Phone, Payment)"
            sess["stage"] = 1

    chat_sessions[key] = sess
    return jsonify({"reply": reply, "done": done})

@app.route("/c/<slug>")
@app.route("/chat/<slug>")
@app.route("/shop/<slug>")
def chat_page(slug):
    vendor = get_vendor_by_slug(slug)
    return render_template_string(CHAT_HTML, shop_name=vendor.get('name','Shop'), location=vendor.get('location','PH City'), slug=slug)

# --- Your Original Telegram Handlers (Kept) ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to CityLords PH City! 🍔\nUse /menu to see vendors\n\nYour 24/7 chat link: /yourapp.onrender.com/c/your-shop-name")

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not supabase:
        await update.message.reply_text("DB not connected")
        return
    try:
        res = supabase.table("vendors").select("*").execute()
        vendors = res.data or []
        if not vendors:
            await update.message.reply_text("No vendors yet. Admin add with /addvendor")
            return
        text = "🏙️ CityLords Vendors + 24/7 Links:\n\n"
        for v in vendors:
            slug = v.get('name','').lower().replace(' ','-')
            text += f"• {v.get('name')} - {v.get('location')}\n Link: /c/{slug}\n Put this in TikTok bio as 'Chat 24/7'\n\n"
        await update.message.reply_text(text)
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID:
        await update.message.reply_text(f"You are not admin ❌\nYour ID: {update.effective_user.id}")
        return
    await update.message.reply_text("✅ Admin Panel\n/addvendor name location phone\n/vendors\n/menu\n\nNEW: Vendors should use /c/shop-name in TikTok bio")

async def add_vendor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID:
        await update.message.reply_text("Not admin")
        return
    if len(context.args) < 3:
        await update.message.reply_text("Usage: /addvendor name location phone")
        return
    name, location, phone = context.args[0], context.args[1], context.args[2]
    try:
        supabase.table("vendors").insert({"name": name, "location": location, "phone": phone}).execute()
        slug = name.lower().replace(' ','-')
        await update.message.reply_text(f"✅ Added: {name}\n24/7 Chat Link: /c/{slug}\nTell vendor to put this link in TikTok bio with title 'Message Us Instantly'")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

async def list_vendors(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID: return
    try:
        res = supabase.table("vendors").select("*").execute()
        await update.message.reply_text(f"Total Vendors: {len(res.data or [])}\nLive Orders in Memory: {len(chat_sessions)}")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

def run_bot():
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        application = Application.builder().token(BOT_TOKEN).build()
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("menu", menu))
        application.add_handler(CommandHandler("admin", admin_panel))
        application.add_handler(CommandHandler("addvendor", add_vendor))
        application.add_handler(CommandHandler("vendors", list_vendors))
        print("Bot polling started...")
        application.run_polling(drop_pending_updates=True, close_loop=False)
    except Exception as e:
        print(f"Bot crashed: {e}")

if not hasattr(app, 'bot_thread_started'):
    threading.Thread(target=run_bot, daemon=True, name="CityLordsBot").start()
    app.bot_thread_started = True

@app.route("/")
def home():
    count = 0
    try:
        if supabase:
            res = supabase.table("vendors").select("*", count="exact").execute()
            count = res.count if res.count is not None else len(res.data or [])
    except: pass
    return f"""
    <h1>CityLords Live ✅</h1>
    <p>Vendors: {count} | Bot: RUNNING | 24/7 Chat: ACTIVE</p>
    <p>Example TikTok Bio Link: <a href="/c/mama-gold">/c/mama-gold</a></p>
    <p>Vendors no longer need to upload products - just share chat link</p>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
