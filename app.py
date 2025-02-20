import os
import json
import requests
import time
import hmac
import hashlib
import random
import re
from flask import Flask, request, jsonify
from bs4 import BeautifulSoup

app = Flask(__name__)

# Load Environment Variables
LINE_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
SHOPEE_AFFILIATE_ID = os.getenv("SHOPEE_AFFILIATE_ID")
LAZADA_AFFILIATE_ID = os.getenv("LAZADA_AFFILIATE_ID")
LAZADA_APP_KEY = os.getenv("LAZADA_APP_KEY")
LAZADA_APP_SECRET = os.getenv("LAZADA_APP_SECRET")
LAZADA_USER_TOKEN = os.getenv("LAZADA_USER_TOKEN")

# ✅ 1️⃣ Shopee: Web Scraping หาสินค้าที่ขายดีที่สุด
def get_shopee_best_selling_product(keyword):
    search_url = f"https://shopee.co.th/search?keyword={keyword}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    product_links = []
    for a_tag in soup.find_all("a", href=True):
        if re.search(r"/product/\d+/\d+", a_tag["href"]):
            product_links.append("https://shopee.co.th" + a_tag["href"])

    return random.choice(product_links) if product_links else search_url

# ✅ 2️⃣ Lazada: ใช้ API หาสินค้าที่ขายดีที่สุด
def get_lazada_best_selling_product(keyword):
    if not all([LAZADA_APP_KEY, LAZADA_APP_SECRET, LAZADA_USER_TOKEN]):
        return "❌ ไม่สามารถสร้างลิงก์ Lazada ได้"

    url = "https://api.lazada.co.th/rest"
    timestamp = int(time.time() * 1000)
    params = {
        "app_key": LAZADA_APP_KEY,
        "sign_method": "sha256",
        "timestamp": timestamp,
        "method": "GET",
        "access_token": LAZADA_USER_TOKEN,
        "keyword": keyword,
        "sort_by": "sales_volume"  # จัดเรียงตามยอดขายสูงสุด
    }

    # สร้าง Signature
    sign_string = "&".join([f"{k}={params[k]}" for k in sorted(params)]) + LAZADA_APP_SECRET
    params["sign"] = hmac.new(LAZADA_APP_SECRET.encode("utf-8"), sign_string.encode("utf-8"), hashlib.sha256).hexdigest()

    response = requests.get(url, params=params)
    data = response.json()

    if "products" in data and len(data["products"]) > 0:
        best_product = data["products"][0]  # เลือกสินค้าที่ขายดีที่สุด
        return f"https://www.lazada.co.th/products/{best_product['product_id']}.html"
    else:
        return f"https://www.lazada.co.th/catalog/?q={keyword}"

# ✅ 3️⃣ Webhook สำหรับรับข้อความจาก LINE
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    events = data.get("events", [])

    for event in events:
        if event.get("type") == "message" and event["message"].get("type") == "text":
            user_id = event["source"]["userId"]
            text = event["message"]["text"]
            reply_token = event["replyToken"]

            shopee_link = get_shopee_best_selling_product(text)
            lazada_link = get_lazada_best_selling_product(text)

            response_text = (f"🔎 ค้นหาสินค้าเกี่ยวกับ: {text}\n\n"
                             f"🛒 Shopee: \n➡️ {shopee_link}\n\n"
                             f"🛍 Lazada: \n➡️ {lazada_link}\n\n"
                             f"🔥 โปรโมชั่นมาแรง! รีบสั่งซื้อตอนนี้ก่อนสินค้าหมด 🔥")

            send_line_message(reply_token, response_text)
    return jsonify({"status": "ok"})

# ✅ 4️⃣ ส่งข้อความกลับไปยัง LINE
def send_line_message(reply_token, text):
    url = "https://api.line.me/v2/bot/message/reply"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
    }
    payload = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": text}]
    }
    requests.post(url, headers=headers, json=payload)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
