import os
import asyncio
import threading
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from supabase import create_client, Client

# --- Config ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
ADMIN_ID_STR = os.getenv("ADMIN_ID", "0")

if not BOT_TOKEN or not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: Missing ENV vars! Check BOT_TOKEN, SUPABASE_URL, SUPABASE_KEY")
else:
    print("ENV loaded OK")

try:
    ADMIN_ID = int(ADMIN_ID_STR)
except:
    ADMIN_ID = 0
    print(f"WARN: ADMIN_ID invalid: {ADMIN_ID_STR}")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None
app = Flask(__name__)

# --- Telegram Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to CityLords PH City! 🍔\nUse /menu to see vendors")

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
        text = "🏙️ CityLords Vendors:\n\n"
        for v in vendors:
            text += f"• {v.get('name')} - {v.get('location')} ({v.get('phone')})\n"
        await update.message.reply_text(text)
    except Exception as e:
        await update.message.reply_text(f"Error loading menu: {e}")

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID:
        await update.message.reply_text(f"You are not admin ❌\nYour ID: {update.effective_user.id}")
        return
    await update.message.reply_text("✅ Admin Panel\n\nCommands:\n/addvendor name location phone\n/vendors\n/menu")

async def add_vendor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID:
        await update.message.reply_text("Not admin")
        return
    if len(context.args) < 3:
        await update.message.reply_text("Usage: /addvendor name location phone\nExample: /addvendor mama_put phcity 08012345678")
        return
    name, location, phone = context.args[0], context.args[1], context.args[2]
    try:
        supabase.table("vendors").insert({"name": name, "location": location, "phone": phone}).execute()
        await update.message.reply_text(f"✅ Added vendor: {name}")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

async def list_vendors(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID:
        return
    try:
        res = supabase.table("vendors").select("*").execute()
        await update.message.reply_text(f"Total Vendors: {len(res.data or [])}")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

def run_bot():
    try:
        # Critical fix for gunicorn thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        application = Application.builder().token(BOT_TOKEN).build()
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("menu", menu))
        application.add_handler(CommandHandler("admin", admin_panel))
        application.add_handler(CommandHandler("addvendor", add_vendor))
        application.add_handler(CommandHandler("vendors", list_vendors))

        print("Bot polling started...")
        # drop_pending_updates fixes Conflict error
        application.run_polling(drop_pending_updates=True, close_loop=False)
    except Exception as e:
        print(f"Bot crashed: {e}")

# Start bot in background for both Flask and Gunicorn
if not hasattr(app, 'bot_thread_started'):
    threading.Thread(target=run_bot, daemon=True, name="CityLordsBot").start()
    app.bot_thread_started = True
    print("Bot thread launched")

@app.route("/")
def home():
    count = 0
    try:
        if supabase:
            res = supabase.table("vendors").select("*", count="exact").execute()
            count = res.count if res.count is not None else len(res.data or [])
    except:
        pass
    return f"<h1>Citylords Live.</h1><p>Vendors: {count}</p><p>Bot: RUNNING ✅</p><p>Free Tier: Web Service (No $7) ✅</p>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
