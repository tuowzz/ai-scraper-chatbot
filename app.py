import requests
from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)

# ตั้งค่า API Key จาก Environment Variables
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
SHOPEE_AFFILIATE_ID = os.getenv("SHOPEE_AFFILIATE_ID", "15384150058")
LINE_REPLY_URL = "https://api.line.me/v2/bot/message/reply"

if not LINE_CHANNEL_ACCESS_TOKEN:
    print("⚠️ LINE_CHANNEL_ACCESS_TOKEN is missing. Please set it in environment variables.")
    sys.exit(1)

def get_shopee_affiliate_link():
    return f"https://s.shopee.co.th/{SHOPEE_AFFILIATE_ID}"

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
    
    shopee_link = get_shopee_affiliate_link()
    response_message = f"👉 คลิกที่นี่เพื่อไปยัง Shopee: {shopee_link}"
    
    # ส่งข้อความตอบกลับไปยัง LINE
    status = reply_to_line(reply_token, response_message)
    
    return jsonify({"status": status, "reply": response_message})

if __name__ == "__main__":
    app.run(port=5000)
