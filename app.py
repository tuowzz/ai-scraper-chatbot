import requests
from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)

# ตั้งค่า API Key จาก Environment Variables
SHOPEE_AFFILIATE_ID = os.getenv("SHOPEE_AFFILIATE_ID", "15384150058")
LAZADA_AFFILIATE_ID = os.getenv("LAZADA_AFFILIATE_ID", "272261049")
TIKTOK_AFFILIATE_ID = os.getenv("TIKTOK_AFFILIATE_ID", "7494437765104241417")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_REPLY_URL = "https://api.line.me/v2/bot/message/reply"

if not LINE_CHANNEL_ACCESS_TOKEN:
    print("⚠️ LINE_CHANNEL_ACCESS_TOKEN is missing. Please set it in environment variables.")
    sys.exit(1)

# ฟังก์ชันสร้างลิงก์ค้นหาสินค้า
def generate_affiliate_links(keyword):
    search_term = keyword.replace(" ", "+")
    
    shopee_link = f"https://shopee.co.th/search?keyword={search_term}&af_id={SHOPEE_AFFILIATE_ID}"
    lazada_link = f"https://www.lazada.co.th/catalog/?q={search_term}&sub_aff_id={LAZADA_AFFILIATE_ID}"
    tiktok_link = f"https://s.tiktok.com/search?q={search_term}&aid={TIKTOK_AFFILIATE_ID}"
    
    return shopee_link, lazada_link, tiktok_link

# ฟังก์ชันส่งข้อความกลับไปยัง LINE
def reply_to_line(reply_token, message):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    payload = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": message}]
    }
    response = requests.post(LINE_REPLY_URL, headers=headers, data=json.dumps(payload))
    return response.status_code

# LINE Webhook
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    if "events" not in data or not data["events"]:
        return jsonify({"error": "Invalid request"}), 400
    
    event = data["events"][0]
    user_message = event.get("message", {}).get("text", "")
    reply_token = event.get("replyToken", "")
    
    if not user_message or not reply_token:
        return jsonify({"error": "No message received"}), 400
    
    shopee_link, lazada_link, tiktok_link = generate_affiliate_links(user_message)
    
    response_message = (f"\U0001F50D ค้นหาสินค้าเกี่ยวกับ: {user_message}\n\n"
                         f"🛒 Shopee: {shopee_link}\n"
                         f"🛍 Lazada: {lazada_link}\n"
                         f"🎵 TikTok Shop: {tiktok_link}")
    
    # ส่งข้อความตอบกลับไปยัง LINE
    status = reply_to_line(reply_token, response_message)
    
    return jsonify({"status": status, "reply": response_message})

if __name__ == "__main__":
    app.run(port=5000)
