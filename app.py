import os
import json
import requests
import time  
import hashlib  
from flask import Flask, request, jsonify

app = Flask(__name__)

# Load environment variables
LINE_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
SHOPEE_AFFILIATE_ID = os.getenv("SHOPEE_AFFILIATE_ID")
LAZADA_AFFILIATE_APP_KEY = os.getenv("LAZADA_AFFILIATE_APP_KEY", "")
LAZADA_AFFILIATE_SECRET = os.getenv("LAZADA_AFFILIATE_SECRET", "")
LAZADA_AFFILIATE_USER_TOKEN = os.getenv("LAZADA_AFFILIATE_USER_TOKEN", "")

# Shopee Affiliate Link (Full Link)
def generate_shopee_link(keyword):
    base_url = "https://shopee.co.th/search"
    return f"{base_url}?keyword={keyword}&af_id={SHOPEE_AFFILIATE_ID}"

# Lazada API Call for Affiliate Link
def generate_lazada_link(keyword):
    if not LAZADA_AFFILIATE_SECRET:
        return "❌ Error: Missing Lazada API credentials"

    lazada_api_url = "https://api.lazada.com/rest"
    params = {
        "app_key": LAZADA_AFFILIATE_APP_KEY or "",
        "sign_method": "sha256",
        "timestamp": str(int(time.time() * 1000)),  
        "keyword": keyword or "",
        "user_token": LAZADA_AFFILIATE_USER_TOKEN or ""
    }

    try:
        # Generate Signature
        sorted_params = sorted(params.items())
        sign_string = LAZADA_AFFILIATE_SECRET + "".join(f"{k}{v}" for k, v in sorted_params) + LAZADA_AFFILIATE_SECRET
        params["sign"] = hashlib.sha256(sign_string.encode()).hexdigest()

        response = requests.get(lazada_api_url, params=params)
        if response.status_code == 200:
            data = response.json()
            if "data" in data and "product_url" in data["data"]:
                return data["data"]["product_url"]
        return "https://www.lazada.co.th/"
    
    except Exception as e:
        return f"❌ Error: {str(e)}"

# Process LINE Messages
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    events = data.get("events", [])

    if not events:
        return jsonify({"status": "no_events"})

    for event in events:
        if event.get("type") == "message" and "message" in event and event["message"].get("type") == "text":
            user_id = event["source"]["userId"]
            text = event["message"]["text"].strip()
            reply_token = event["replyToken"]

            # Generate Affiliate Links
            shopee_link = generate_shopee_link(text)
            lazada_link = generate_lazada_link(text)

            # Construct Response Message
            response_text = (
                f"🔎 ค้นหาสินค้าเกี่ยวกับ: {text}\n\n"
                f"🛒 Shopee: \n➡️ {shopee_link}\n\n"
                f"🛍 Lazada: \n➡️ {lazada_link}\n\n"
                f"🔥 โปรโมชั่นมาแรง! รีบสั่งซื้อตอนนี้ก่อนสินค้าหมด 🔥"
            )

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
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code != 200:
        print(f"Error sending message: {response.text}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
