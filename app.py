import os
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# โหลด Environment Variables
LINE_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
SHOPEE_AFFILIATE_ID = os.getenv("SHOPEE_AFFILIATE_ID")
LAZADA_AFFILIATE_ID = os.getenv("LAZADA_AFFILIATE_ID")
LAZADA_APP_KEY = os.getenv("LAZADA_APP_KEY")
LAZADA_APP_SECRET = os.getenv("LAZADA_APP_SECRET")
LAZADA_USER_TOKEN = os.getenv("LAZADA_USER_TOKEN")

# โหลดข้อมูลสินค้า (ถ้ามีไฟล์)
script_dir = os.path.dirname(__file__)
file_path = os.path.join(script_dir, "products.json")

if os.path.exists(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        product_data = json.load(f)
else:
    product_data = {}  # ใช้ค่าเริ่มต้นเป็น dict ว่าง

# Shopee Affiliate Link
def generate_shopee_link(keyword):
    if keyword in product_data and "shopee" in product_data[keyword]:
        seller_id = product_data[keyword]["shopee"]["seller_id"]
        product_id = product_data[keyword]["shopee"]["product_id"]
        return f"https://shopee.co.th/product/{seller_id}/{product_id}?af_id={SHOPEE_AFFILIATE_ID}"
    return f"https://shopee.co.th/search?keyword={keyword}&af_id={SHOPEE_AFFILIATE_ID}"

# Lazada Affiliate Link
def generate_lazada_link(keyword):
    if LAZADA_APP_KEY and LAZADA_APP_SECRET and LAZADA_USER_TOKEN:
        return f"https://www.lazada.co.th/catalog/?q={keyword}&sub_aff_id={LAZADA_AFFILIATE_ID}"
    return f"❌ ไม่สามารถสร้างลิงก์ Lazada ได้"

# Webhook LINE Bot
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    events = data.get("events", [])

    for event in events:
        if event.get("type") == "message" and event["message"].get("type") == "text":
            user_id = event["source"]["userId"]
            text = event["message"]["text"]
            reply_token = event["replyToken"]

            shopee_link = generate_shopee_link(text)
            lazada_link = generate_lazada_link(text)

            response_text = (f"🔎 ค้นหาสินค้าเกี่ยวกับ: {text}\n\n"
                             f"🛒 Shopee: \n➡️ {shopee_link}\n\n"
                             f"🛍 Lazada: \n➡️ {lazada_link}\n\n"
                             f"🔥 โปรโมชั่นมาแรง! รีบสั่งซื้อตอนนี้ก่อนสินค้าหมด 🔥")

            send_line_message(reply_token, response_text)
    return jsonify({"status": "ok"})

# ส่งข้อความกลับไปยัง LINE
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
