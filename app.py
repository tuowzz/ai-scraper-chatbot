import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# ตั้งค่า Environment Variables
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_REPLY_URL = "https://api.line.me/v2/bot/message/reply"

if not LINE_CHANNEL_ACCESS_TOKEN:
    print("⚠️ LINE_CHANNEL_ACCESS_TOKEN is missing. Please set it in environment variables.")
    exit(1)

@app.route("/")
def home():
    return "AI Scraper Chatbot is running!"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    if not data or "events" not in data:
        return jsonify({"error": "Invalid request"}), 400

    # รับข้อความจาก LINE
    event = data["events"][0]
    user_message = event.get("message", {}).get("text", "")
    reply_token = event.get("replyToken", "")

    if not user_message or not reply_token:
        return jsonify({"error": "No message received"}), 400

    # ใช้ OpenAI ตอบกลับข้อความ
    ai_reply = chat_with_ai(user_message)

    # ส่งข้อความตอบกลับไปยัง LINE
    status = reply_to_line(reply_token, ai_reply)

    return jsonify({"status": status, "reply": ai_reply}), 200

def chat_with_ai(user_message):
    """ใช้ AI ตอบกลับข้อความ"""
    return f"คุณพิมพ์ว่า: {user_message}"  # เปลี่ยนเป็น OpenAI API ได้

def reply_to_line(reply_token, message):
    """ส่งข้อความกลับไปยัง LINE"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    payload = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": message}]
    }
    response = requests.post(LINE_REPLY_URL, headers=headers, json=payload)
    return response.status_code

if name == "__main__":
    app.run(host="0.0.0.0", port=5000)
