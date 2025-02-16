import os
import json
import requests
import time
import hmac
import hashlib
from flask import Flask, request, jsonify

app = Flask(__name__)

# Load environment variables
LINE_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
SHOPEE_AFFILIATE_ID = os.getenv("SHOPEE_AFFILIATE_ID")
LAZADA_AFFILIATE_ID = os.getenv("LAZADA_AFFILIATE_ID")
BITLY_ACCESS_TOKEN = os.getenv("BITLY_ACCESS_TOKEN")

# Shopee Affiliate Link
def generate_shopee_link(keyword):
    return f"https://shopee.co.th/search?keyword={keyword}&af_id={SHOPEE_AFFILIATE_ID}"

# Lazada Search URL (แทน API)
def generate_lazada_link(keyword):
    return f"https://www.lazada.co.th/catalog/?q={keyword}&sub_aff_id={LAZADA_AFFILIATE_ID}"

# ย่อลิงก์ด้วย Bitly API
def shorten_link(url):
    if not BITLY_ACCESS_TOKEN:
        return url  # ถ้าไม่มี Bitly Token ให้ใช้ลิงก์ยาว
    
    headers = {
        "Authorization": f"Bearer {BITLY_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {"long_url": url}
    response = requests.post("https://api-ssl.bitly.com/v4/shorten", json=data, headers=headers)
    return response.json().get("link", url)

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
            
            shopee_link = generate_shopee_link(text)
            lazada_link = generate_lazada_link(text)
            
            # ย่อลิงก์ถ้าใช้ Bitly
            shopee_link = shorten_link(shopee_link)
            lazada_link = shorten_link(lazada_link)
            
            response_text = (f"🔎 ค้นหาสินค้าเกี่ยวกับ: {text}\n\n"
                             f"🛒 Shopee: \n➡️ {shopee_link}\n\n"
                             f"🛍 Lazada: \n➡️ {lazada_link}\n\n"
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
