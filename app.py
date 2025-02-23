import os
import json
import time
import hmac
import hashlib
import requests
import urllib.parse
from flask import Flask, request, jsonify
from bs4 import BeautifulSoup

app = Flask(__name__)

# ✅ โหลด Environment Variables (API Keys)
LINE_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
SHOPEE_AFFILIATE_ID = os.getenv("SHOPEE_AFFILIATE_ID")
LAZADA_AFFILIATE_ID = os.getenv("LAZADA_AFFILIATE_ID")
LAZADA_APP_KEY = os.getenv("LAZADA_APP_KEY")
LAZADA_APP_SECRET = os.getenv("LAZADA_APP_SECRET")
LAZADA_USER_TOKEN = os.getenv("LAZADA_USER_TOKEN")

# ✅ ฟังก์ชันดึง "สินค้าขายดีที่สุด" จาก Lazada API และสร้างลิงก์ Affiliate
def get_best_selling_lazada(keyword):
    params = {
        "app_key": LAZADA_APP_KEY,
        "timestamp": str(int(time.time() * 1000)),
        "sign_method": "sha256",
        "access_token": LAZADA_USER_TOKEN,
        "method": "lazada.product.search",
        "format": "JSON",
        "v": "1.0",
        "q": keyword,
        "sort_by": "sales_volume"
    }

    # 🔹 สร้าง Signature สำหรับ Lazada API
    sorted_params = sorted(params.items(), key=lambda x: x[0])
    base_string = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in sorted_params)
    signature = hmac.new(
        LAZADA_APP_SECRET.encode(), base_string.encode(), hashlib.sha256
    ).hexdigest().upper()

    params["sign"] = signature
    url = "https://api.lazada.co.th/rest?" + "&".join(f"{k}={v}" for k, v in params.items())

    response = requests.get(url).json()
    
    if "data" in response and "products" in response["data"]:
        best_product = response["data"]["products"][0]
        product_id = best_product["product_id"]
        return product_id, best_product["name"]
    
    return None, None

# ✅ ฟังก์ชันสร้างลิงก์ Affiliate จาก Lazada API
def generate_lazada_affiliate_link(product_id):
    params = {
        "app_key": LAZADA_APP_KEY,
        "timestamp": str(int(time.time() * 1000)),
        "sign_method": "sha256",
        "access_token": LAZADA_USER_TOKEN,
        "method": "lazada.generate.afflink",
        "format": "JSON",
        "v": "1.0",
        "tracking_id": LAZADA_AFFILIATE_ID,
        "url": f"https://www.lazada.co.th/products/{product_id}.html"
    }

    # 🔹 สร้าง Signature
    sorted_params = sorted(params.items(), key=lambda x: x[0])
    base_string = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in sorted_params)
    signature = hmac.new(
        LAZADA_APP_SECRET.encode(), base_string.encode(), hashlib.sha256
    ).hexdigest().upper()

    params["sign"] = signature
    url = "https://api.lazada.co.th/rest?" + "&".join(f"{k}={v}" for k, v in params.items())

    response = requests.get(url).json()
    
    if "data" in response and "aff_link" in response["data"]:
        return response["data"]["aff_link"]
    
    return None

# ✅ ฟังก์ชันดึง "สินค้าขายดีที่สุด" จาก Shopee (Web Scraping)
def get_best_selling_shopee(keyword):
    search_url = f"https://shopee.co.th/search?keyword={keyword}"
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    product_links = []
    for a_tag in soup.find_all("a", href=True):
        if "/product/" in a_tag["href"]:
            product_links.append("https://shopee.co.th" + a_tag["href"])

    return product_links[0] if product_links else search_url

# ✅ Webhook สำหรับ LINE Bot หรือ Telegram Bot
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    events = data.get("events", [])

    for event in events:
        if event.get("type") == "message" and event["message"].get("type") == "text":
            user_id = event["source"]["userId"]
            text = event["message"]["text"]
            reply_token = event["replyToken"]

            # ✅ ดึงสินค้าขายดีที่สุดจาก Shopee
            shopee_link = get_best_selling_shopee(text)

            # ✅ ดึงสินค้าขายดีที่สุดจาก Lazada + สร้างลิงก์ Affiliate
            product_id, product_name = get_best_selling_lazada(text)
            lazada_link = generate_lazada_affiliate_link(product_id) if product_id else f"https://www.lazada.co.th/catalog/?q={text}&sub_aff_id={LAZADA_AFFILIATE_ID}"

            # ✅ ส่งข้อความตอบกลับ
            response_text = (f"🔎 ค้นหาสินค้าเกี่ยวกับ: {text}\n\n"
                             f"🛒 Shopee: \n➡️ {shopee_link}\n\n"
                             f"🛍 Lazada: \n➡️ {lazada_link}\n\n"
                             f"🔥 โปรโมชั่นมาแรง! รีบสั่งซื้อตอนนี้ก่อนสินค้าหมด 🔥")

            send_line_message(reply_token, response_text)

    return jsonify({"status": "ok"})

# ✅ ฟังก์ชันส่งข้อความกลับไปยัง LINE
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
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
