import requests
from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)

# ตั้งค่า API Key และ Affiliate ID
SHOPEE_AFFILIATE_ID = "15384150058"  # ใส่ Affiliate ID ที่ถูกต้อง
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")

LINE_REPLY_URL = "https://api.line.me/v2/bot/message/reply"

if not LINE_CHANNEL_ACCESS_TOKEN:
    print("⚠️ LINE_CHANNEL_ACCESS_TOKEN is missing. Please set it in environment variables.")
    exit(1)

# ฟังก์ชันสร้างลิงก์ค้นหา Shopee
def get_shopee_search_link(keyword):
    base_url = "https://shopee.co.th/search"
    return f"{base_url}?keyword={keyword}&af_id={SHOPEE_AFFILIATE_ID}"

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

    # สร้างลิงก์ Shopee
    search_link = get_shopee_search_link(user_message)
    response_message = f"🔎 ค้นหาสินค้าเกี่ยวกับ: {user_message}\n👉 ลิงก์ Shopee (Affiliate): {search_link}"

    # ส่งข้อความตอบกลับไปยัง LINE
    status = reply_to_line(reply_token, response_message)

    return jsonify({"status": status, "reply": response_message})

if __name__ == "__main__":
    app.run(port=5000)
