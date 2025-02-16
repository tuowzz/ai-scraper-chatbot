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
LAZADA_APP_KEY = os.getenv("LAZADA_APP_KEY")
LAZADA_APP_SECRET = os.getenv("LAZADA_APP_SECRET")
LAZADA_USER_TOKEN = os.getenv("LAZADA_USER_TOKEN")
LAZADA_AFFILIATE_ID = os.getenv("LAZADA_AFFILIATE_ID")

# Shopee Affiliate Link
def generate_shopee_link(keyword):
    return f"https://shopee.co.th/search?keyword={keyword}&af_id={SHOPEE_AFFILIATE_ID}"

# Lazada LiteApp API - Generate Affiliate Link
def generate_lazada_link(keyword):
    try:
        base_url = "https://api.lazada.co.th/rest"
        endpoint = "/promotion/link/get"
        timestamp = str(int(time.time() * 1000))
        
        params = {
            "app_key": LAZADA_APP_KEY,
            "sign_method": "sha256",
            "timestamp": timestamp,
            "access_token": LAZADA_USER_TOKEN,
            "url": f"https://www.lazada.co.th/catalog/?q={keyword}",
            "sub_aff_id": LAZADA_AFFILIATE_ID
        }

        sorted_params = sorted(params.items())
        query_string = "&".join(f"{k}={v}" for k, v in sorted_params)
        sign = hmac.new(LAZADA_APP_SECRET.encode(), query_string.encode(), hashlib.sha256).hexdigest().upper()
        params["sign"] = sign

        response = requests.get(base_url + endpoint, params=params)
        response_data = response.json()

        if "data" in response_data and "shortLink" in response_data["data"]:
            return response_data["data"]["shortLink"]
        else:
            return "❌ ไม่สามารถสร้างลิงก์ Lazada ได้"
    except Exception as e:
        return f"❌ Error: {str(e)}"

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
