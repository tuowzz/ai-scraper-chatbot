import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Load environment variables
LAZADA_AFFILIATE_ID = os.getenv("LAZADA_AFFILIATE_ID")
LAZADA_APP_KEY = os.getenv("LAZADA_APP_KEY")
LAZADA_APP_SECRET = os.getenv("LAZADA_APP_SECRET")
LAZADA_USER_TOKEN = os.getenv("LAZADA_USER_TOKEN")
SHOPEE_AFFILIATE_ID = os.getenv("SHOPEE_AFFILIATE_ID")

# Shopee Search URL
SHOPEE_SEARCH_URL = "https://shopee.co.th/search?keyword={}&af_id=" + SHOPEE_AFFILIATE_ID

# Lazada Search API
LAZADA_SEARCH_URL = "https://api.lazada.com/rest?app_key={}&sign_method=sha256"

# Function to shorten URLs using Bitly or Lazada's shortener
def shorten_url(long_url):
    try:
        response = requests.post("https://api-ssl.bitly.com/v4/shorten",
                                 headers={"Authorization": f"Bearer {os.getenv('BITLY_ACCESS_TOKEN')}"},
                                 json={"long_url": long_url})
        if response.status_code == 200:
            return response.json().get("link")
        return long_url  # Fallback to original URL if shortener fails
    except Exception:
        return long_url

# Function to get Lazada deep link
def get_lazada_deep_link(keyword):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LAZADA_USER_TOKEN}"
    }
    params = {
        "q": keyword,
        "app_key": LAZADA_APP_KEY,
        "sign_method": "sha256"
    }
    response = requests.get(LAZADA_SEARCH_URL.format(LAZADA_APP_KEY), headers=headers, params=params)
    if response.status_code == 200:
        items = response.json().get("data", {}).get("items", [])
        if items:
            product_url = items[0]["url"]
            return shorten_url(product_url)
    return "https://www.lazada.co.th/catalog/?q={}&sub_aff_id={}".format(keyword, LAZADA_AFFILIATE_ID)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    user_message = data.get("message", "").strip()
    
    shopee_link = shorten_url(SHOPEE_SEARCH_URL.format(user_message))
    lazada_link = get_lazada_deep_link(user_message)
    
    response_message = (
        f"🔎 ค้นหาสินค้าเกี่ยวกับ: {user_message}\n\n"
        f"🛒 Shopee: \n➡️ {shopee_link}\n\n"
        f"🛍 Lazada: \n➡️ {lazada_link}\n\n"
        f"📢 🔥 โปรโมชั่นมาแรง! รีบสั่งซื้อตอนนี้ก่อนสินค้าหมด 🔥"
    )
    
    return jsonify({"reply": response_message})

if __name__ == "__main__":
    app.run(debug=True)
