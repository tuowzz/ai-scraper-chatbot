import os
import json
import requests
from flask import Flask, request, jsonify
from urllib.parse import quote
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

# โหลด Environment Variables
LINE_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
SHOPEE_AFFILIATE_ID = os.getenv("SHOPEE_AFFILIATE_ID")
LAZADA_AFFILIATE_ID = os.getenv("LAZADA_AFFILIATE_ID")

# ✅ ค้นหาสินค้าขายดีที่สุดใน Shopee
def get_best_selling_shopee_product(keyword):
    search_url = f"https://shopee.co.th/search?keyword={quote(keyword)}"
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    products = []
    for a_tag in soup.find_all("a", href=True):
        match = re.search(r"/product/(\d+)/(\d+)", a_tag["href"])
        if match:
            seller_id, product_id = match.groups()
            products.append({
                "link": f"https://shopee.co.th/product/{seller_id}/{product_id}?af_id={SHOPEE_AFFILIATE_ID}",
                "sold": int(a_tag.get_text(strip=True).replace("ขายแล้ว", "").replace("พัน", "000").replace("+", ""))
            })

    if products:
        best_product = max(products, key=lambda x: x["sold"])
        return best_product["link"]
    return search_url  # ถ้าไม่มีสินค้า ส่งลิงก์ค้นหาแทน

# ✅ ค้นหาสินค้าขายดีที่สุดใน Lazada
def get_best_selling_lazada_product(keyword):
    search_url = f"https://www.lazada.co.th/catalog/?q={quote(keyword)}&sub_aff_id={LAZADA_AFFILIATE_ID}"
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    products = []
    for a_tag in soup.find_all("a", href=True):
        if re.search(r"/products/.*?-\d+.html", a_tag["href"]):
            products.append("https:" + a_tag["href"])

    return products[0] if products else search_url  # ถ้าไม่มีสินค้า ส่งลิงก์ค้นหาแทน

# 📌 Webhook LINE Bot
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    events = data.get("events", [])

    for event in events:
        if event.get("type") == "message" and event["message"].get("type") == "text":
            user_id = event["source"]["userId"]
            text = event["message"]["text"]
            reply_token = event["replyToken"]

            shopee_link = get_best_selling_shopee_product(text)
            lazada_link = get_best_selling_lazada_product(text)

            response_text = (f"🔎 ค้นหาสินค้าเกี่ยวกับ: {text}\n\n"
                             f"🛒 Shopee (ขายดีที่สุด): \n➡️ {shopee_link}\n\n"
                             f"🛍 Lazada (ขายดีที่สุด): \n➡️ {lazada_link}\n\n"
                             f"🔥 โปรโมชั่นมาแรง! รีบสั่งซื้อตอนนี้ก่อนสินค้าหมด 🔥")

            send_line_message(reply_token, response_text)
    return jsonify({"status": "ok"})

# 📌 ส่งข้อความกลับไปยัง LINE
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
