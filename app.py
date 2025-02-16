import os
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Load environment variables
LINE_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
SHOPEE_AFFILIATE_ID = os.getenv("SHOPEE_AFFILIATE_ID")
LAZADA_AFFILIATE_ID = os.getenv("LAZADA_AFFILIATE_ID")
BITLY_ACCESS_TOKEN = os.getenv("BITLY_ACCESS_TOKEN")

# Shopee Flash Sale Link (ไม่ใช้ API)
def generate_shopee_flashsale_link():
    return f"https://shopee.co.th/m/flash_sale?af_id={SHOPEE_AFFILIATE_ID}"

# Lazada Flash Sale Link (ไม่ใช้ API)
def generate_lazada_flashsale_link():
    return f"https://www.lazada.co.th/deals/?sub_aff_id={LAZADA_AFFILIATE_ID}"

# LINE Webhook
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    events = data.get("events", [])
    
    for event in events:
        if event.get("type") == "message" and event["message"].get("type") == "text":
            user_id = event["source"]["userId"]
            text = event["message"]["text"]
            reply_token = event["replyToken"]
            
            shopee_link = generate_shopee_flashsale_link()
            lazada_link = generate_lazada_flashsale_link()
            
            response_text = (f"🔎 ค้นหาสินค้า Flash Sale ตอนนี้! \n\n"
                             f"🛒 Shopee Flash Sale: \n➡️ {shopee_link}\n\n"
                             f"🛍 Lazada Flash Sale: \n➡️ {lazada_link}\n\n"
                             f"🔥 โปรโมชั่นมาแรง! รีบสั่งซื้อตอนนี้ก่อนสินค้าหมด 🔥")
            
            send_line_message(reply_token, response_text)
    return jsonify({"status": "ok"})

# Send Message to LINE
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
