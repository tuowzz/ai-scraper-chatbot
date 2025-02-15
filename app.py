import os
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# ดึง Shopee Affiliate ID จาก Environment Variables
SHOPEE_AFFILIATE_ID = os.getenv("SHOPEE_AFFILIATE_ID", "9A9ZBqQZk5")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_REPLY_URL = "https://api.line.me/v2/bot/message/reply"

def generate_affiliate_link(product_url):
    """ ฟังก์ชันสร้าง Shopee Affiliate Link """
    return f"https://shope.ee/{SHOPEE_AFFILIATE_ID}?af_click_lookback=7d&af_reengagement_window=30d"

def reply_to_line(reply_token, message):
    """ ฟังก์ชันส่งข้อความกลับไปยัง LINE """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    payload = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": message}]
    }
    requests.post(LINE_REPLY_URL, headers=headers, data=json.dumps(payload))

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

    # ตรวจจับข้อความค้นหา เช่น "หา iPhone ราคาถูก"
    if "หา" in user_message and "Shopee" in user_message:
        # สร้าง Affiliate Link
        affiliate_link = generate_affiliate_link("https://shopee.co.th/")
        ai_reply = f"🔗 ลองดูสินค้าบน Shopee ได้ที่นี่: {affiliate_link}"
    else:
        ai_reply = "ขออภัย ฉันไม่สามารถช่วยคุณได้ในตอนนี้"

    reply_to_line(reply_token, ai_reply)
    return jsonify({"status": "success", "reply": ai_reply})

if __name__ == "__main__":
    app.run(port=5000)
