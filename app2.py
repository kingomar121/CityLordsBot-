from flask import Flask, request
import os
from supabase import create_client

app = Flask(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route("/")
def home():
    return "<h1>CityLords Test Version 2 Works!</h1><a href='/register'>Register</a>"

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        business_name = request.form["business_name"]
        whatsapp = request.form["whatsapp"]
        slug = business_name.lower().replace(" ", "-")
        supabase.table("vendors").insert({"business_name": business_name,"slug": slug,"whatsapp": whatsapp}).execute()
        host = request.host
        link = f"https://{host}/{slug}"
        return f"<h1>Success!</h1><h2>{link}</h2><a href='{link}'>View Shop</a>"
    return """
    <form method="POST">
        <h2>Register Vendor</h2>
        Business Name: <input name="business_name" required><br><br>
        WhatsApp: <input name="whatsapp" required><br><br>
        <button type="submit">Register</button>
    </form>
    """

@app.route("/<slug>")
def vendor_landing(slug):
    vendor = supabase.table("vendors").select("*").eq("slug", slug).execute()
    if not vendor.data:
        return "Shop not found", 404
    vendor = vendor.data[0]
    return f"""
    <div style="text-align:center; padding-top:100px;">
        <h1>{vendor['business_name']}</h1>
        <a href="/{slug}/products"><button style="padding:20px 50px; background:black; color:white; font-size:20px;">Visit Shop</button></a>
        <p>Powered by CityLords</p>
    </div>
    """

@app.route("/<slug>/products")
def vendor_products(slug):
    vendor = supabase.table("vendors").select("*").eq("slug", slug).execute()
    if not vendor.data:
        return "Shop not found", 404
    vendor = vendor.data[0]
    products = supabase.table("products").select("*").eq("vendor_slug", slug).execute().data
    html = f"<a href='/{slug}'>Back</a><h1>{vendor['business_name']} Shop</h1><hr>"
    if not products:
        html += "<p>No products yet</p>"
    for p in products:
        wa_link = f"https://wa.me/{vendor['whatsapp']}?text=Hi, I want {p['name']}"
        html += f"<div style='border:1px solid #ccc; padding:10px; margin:10px;'><h3>{p['name']}</h3><p>{p['price']}</p><a href='{wa_link}'><button>Buy</button></a></div>"
    return html

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
