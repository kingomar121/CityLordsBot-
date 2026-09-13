import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from supabase import create_client, Client

BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_vendor_by_slug(slug):
    res = supabase.table("vendors").select("*").eq("slug", slug).execute()
    return res.data[0] if res.data else None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    user_id = update.effective_user.id
    if args and args[0].startswith("shop_"):
        slug = args[0].replace("shop_", "")
        vendor = get_vendor_by_slug(slug)
        if not vendor:
            await update.message.reply_text("Shop not found.")
            return
        products = supabase.table("products").select("*").eq("vendor_id", vendor["id"]).eq("is_active", True).execute().data
        text = f"Welcome to {vendor['shop_name']}!\n\n{vendor['address']}\n{vendor['faq']}\n"
        buttons = []
        for p in products:
            buttons.append([InlineKeyboardButton(f"{p['name']} - N{p['price']}", callback_data=f"view_{p['id']}")])
        buttons.append([InlineKeyboardButton("View Cart", callback_data=f"cart_{slug}")])
        buttons.append([InlineKeyboardButton("Chat Vendor", url=f"https://wa.me/{vendor['whatsapp']}")])
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))
        return
    vendor_check = supabase.table("vendors").select("*").eq("telegram_id", user_id).execute().data
    if vendor_check:
        await update.message.reply_text(f"Welcome back {vendor_check[0]['shop_name']}! Go to /dashboard")
    else:
        await update.message.reply_text("Welcome to CityLords Bot!")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith("view_"):
        prod_id = data.split("_")[1]
        prod = supabase.table("products").select("*").eq("id", prod_id).execute().data[0]
        text = f"{prod['name']}\n\n{prod['description']}\n\nPrice: N{prod['price']}"
        buttons = [[InlineKeyboardButton("Add to Cart", callback_data=f"add_{prod['id']}_{prod['vendor_id']}")]]
        await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    elif data.startswith("add_"):
        await query.message.reply_text("Added to cart!")

async def dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    vendor = supabase.table("vendors").select("*").eq("telegram_id", user_id).execute().data
    if not vendor:
        await update.message.reply_text("You are not a vendor yet.")
        return
    v = vendor[0]
    text = f"Vendor Dashboard: {v['shop_name']}\n\nYour permanent link:\nt.me/{context.bot.username}?start=shop_{v['slug']}\n\nThis link NEVER changes!"
    buttons = [[InlineKeyboardButton("Edit Shop Name", callback_data="edit_name")],[InlineKeyboardButton("Add Product", callback_data="add_product")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID:
        return
    await update.message.reply_text("Admin: Use /addvendor slug shopname whatsapp")

async def addvendor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID:
        return
    try:
        slug = context.args[0]
        whatsapp = context.args[-1]
        shop_name = " ".join(context.args[1:-1])
        supabase.table("vendors").insert({"slug": slug, "shop_name": shop_name, "whatsapp": whatsapp, "address": "Port Harcourt", "faq": "Delivery 45 mins"}).execute()
        await update.message.reply_text(f"Vendor {shop_name} created! Link: t.me/{context.bot.username}?start=shop_{slug}")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("dashboard", dashboard))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("addvendor", addvendor))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()

if __name__ == "__main__":
    main()
