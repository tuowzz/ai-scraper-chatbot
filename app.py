import os
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# โหลดตัวแปรจาก Environment
LINE_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
SHOPEE_AFFILIATE_ID = os.getenv("SHOPEE_AFFILIATE_ID")
LAZADA_AFFILIATE_ID = os.getenv("LAZADA_AFFILIATE_ID")

# โหลดข้อมูลสินค้า
with open("products.json", "r", encoding="utf-8") as f:
    product_data = json.load(f)

# ฟังก์ชันสร้างลิงก์ Shopee
def generate_shopee_link(keyword):
    if keyword in product_data:
        seller_id = product_data[keyword]["shopee"]["seller_id"]
        product_id = product_data[keyword]["shopee"]["product_id"]
        return f"https://shopee.co.th/product/{seller_id}/{product_id}?af_id={SHOPEE_AFFILIATE_ID}"
    else:
        return f"https://shopee.co.th/search?keyword={keyword}&af_id={SHOPEE_AFFILIATE_ID}"

# ฟังก์ชันสร้างลิงก์ Lazada
def generate_lazada_link(keyword):
    if keyword in product_data:
        product_id = product_data[keyword]["lazada"]["product_id"]
        product_name = product_data[keyword]["lazada"]["name"]
        return f"https://www.lazada.co.th/products/{product_name}-{product_id}.html?sub_aff_id={LAZADA_AFFILIATE_ID}"
    else:
        return f"https://www.lazada.co.th/catalog/?q={keyword}&sub_aff_id={LAZADA_AFFILIATE_ID}"

# Webhook สำหรับ LINE Bot
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

# ฟังก์ชันส่งข้อความกลับ LINE
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
