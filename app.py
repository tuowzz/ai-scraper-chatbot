import requests
import os
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

# 🔑 ตั้งค่า Affiliate ID
SHOPEE_AFFILIATE_ID = "15384150058"
LAZADA_AFFILIATE_ID = "272261049"

# 🔗 ฟังก์ชันสร้างลิงก์ Shopee
def generate_shopee_link(keyword):
    base_url = "https://shopee.co.th/search"
    return f"{base_url}?keyword={keyword}&af_id={SHOPEE_AFFILIATE_ID}"

# 🔗 ฟังก์ชันสร้างลิงก์ Lazada
def generate_lazada_link(keyword):
    base_url = "https://www.lazada.co.th/catalog/"
    return f"{base_url}?q={keyword}&sub_aff_id={LAZADA_AFFILIATE_ID}"

# 📩 ฟังก์ชันตอบกลับข้อความไปยัง LINE
def reply_to_line(reply_token, message):
    LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    payload = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": message}]
    }
    requests.post("https://api.line.me/v2/bot/message/reply", headers=headers, json=payload)

# 🎯 LINE Webhook API
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

    # 🔍 ค้นหาสินค้า
    shopee_link = generate_shopee_link(user_message)
    lazada_link = generate_lazada_link(user_message)

    # 📌 สร้างข้อความตอบกลับ
    reply_message = (
        f"🔎 ค้นหาสินค้าเกี่ยวกับ: {user_message}\n\n"
        f"🛒 Shopee: {shopee_link}\n"
        f"🛍 Lazada: {lazada_link}"
    )

    # ส่งข้อความกลับไปยัง LINE
    reply_to_line(reply_token, reply_message)

    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(port=5000)
