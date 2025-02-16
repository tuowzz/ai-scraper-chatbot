import os
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Load environment variables
LINE_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
SHOPEE_AFFILIATE_ID = os.getenv("SHOPEE_AFFILIATE_ID")
LAZADA_AFFILIATE_ID = os.getenv("LAZADA_AFFILIATE_ID")
TIKTOK_AFFILIATE_ID = os.getenv("TIKTOK_AFFILIATE_ID")

# Shopee Affiliate Link (Shortened)
def generate_shopee_link(keyword):
    base_url = "https://s.shopee.co.th"
    return f"{base_url}/{SHOPEE_AFFILIATE_ID}?keyword={keyword}"

# Lazada Affiliate Link
def generate_lazada_link(keyword):
    base_url = "https://www.lazada.co.th/catalog/"
    return f"{base_url}?q={keyword}&sub_aff_id={LAZADA_AFFILIATE_ID}"

# TikTok Affiliate Link (Correct Format)
def generate_tiktok_link(keyword):
    base_url = "https://www.tiktok.com/search"
    return f"{base_url}?q={keyword}&af_id={TIKTOK_AFFILIATE_ID}"

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

            # Generate Links
            shopee_link = generate_shopee_link(text)
            lazada_link = generate_lazada_link(text)
            tiktok_link = generate_tiktok_link(text)

            # Construct Response
            response_text = (
                f"🔎 ค้นหาสินค้าเกี่ยวกับ: {text}\n\n"
                f"🛒 Shopee: \n➡️ {shopee_link}\n\n"
                f"🛍 Lazada: \n➡️ {lazada_link}\n\n"
                f"🎵 TikTok Shop: \n➡️ {tiktok_link}\n\n"
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
