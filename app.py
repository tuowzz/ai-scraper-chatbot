import requests
try:
    import openai
except ModuleNotFoundError:
    print("⚠️ OpenAI library not found. Please install it using 'pip install openai'")
    import sys
    sys.exit(1)
from flask import Flask, request, jsonify
from bs4 import BeautifulSoup
import json
import os

app = Flask(__name__)

# ตั้งค่า API Key จาก Environment Variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
SHOPEE_AFFILIATE_ID = "15384150058"
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_REPLY_URL = "https://api.line.me/v2/bot/message/reply"

if not OPENAI_API_KEY:
    print("⚠️ OPENAI_API_KEY is missing. Please set it in environment variables.")
    sys.exit(1)
if not LINE_CHANNEL_ACCESS_TOKEN:
    print("⚠️ LINE_CHANNEL_ACCESS_TOKEN is missing. Please set it in environment variables.")
    sys.exit(1)

# ฟังก์ชันสร้างลิงก์ Affiliate ของ Shopee
def generate_shopee_link(keyword):
    return f"https://s.shopee.co.th/{SHOPEE_AFFILIATE_ID}?keyword={keyword}"

# ฟังก์ชันใช้ OpenAI วิเคราะห์คำค้นหา
def chat_with_ai(user_message):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "คุณเป็นแชทบอทแนะนำสินค้า Shopee"},
                {"role": "user", "content": user_message}
            ],
            api_key=OPENAI_API_KEY
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠️ Error occurred while communicating with OpenAI: {str(e)}"

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
    
    # วิเคราะห์คำค้นหา
    ai_reply = chat_with_ai(user_message)
    shopee_link = generate_shopee_link(user_message)
    
    full_reply = f"🔎 ค้นหาสินค้าเกี่ยวกับ: {user_message}\n\n👉 ลิงก์ Shopee (Affiliate): {shopee_link}"
    
    # ส่งข้อความตอบกลับไปยัง LINE
    status = reply_to_line(reply_token, full_reply)
    
    return jsonify({"status": status, "reply": full_reply})

if __name__ == "__main__":
    app.run(port=5000)
