import requests
import logging
from flask import Flask, request, jsonify
from bs4 import BeautifulSoup
import json
import os

# ตั้งค่า Logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

# ตั้งค่า API Key จาก Environment Variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
SHOPEE_AFFILIATE_ID = os.getenv("SHOPEE_AFFILIATE_ID", "9A9ZBqQZk5")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_REPLY_URL = "https://api.line.me/v2/bot/message/reply"

# ตรวจสอบว่า API Keys ถูกต้องหรือไม่
if not OPENAI_API_KEY:
    logging.error("⚠️ OPENAI_API_KEY is missing. Please set it in environment variables.")
    exit(1)
if not LINE_CHANNEL_ACCESS_TOKEN:
    logging.error("⚠️ LINE_CHANNEL_ACCESS_TOKEN is missing. Please set it in environment variables.")
    exit(1)

# ฟังก์ชันดึงข้อมูลจาก Shopee
def scrape_shopee(keyword):
    url = f"https://shopee.co.th/search?keyword={keyword}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        logging.error(f"⚠️ Failed to fetch data from Shopee. Status code: {response.status_code}")
        return []
    
    soup = BeautifulSoup(response.text, "html.parser")
    products = []
    
    for product in soup.find_all("div", class_="shopee-search-item-result__item")[:5]:
        try:
            name = product.find("div", class_="_10Wbs-")
            price = product.find("span", class_="_29R_un")
            if name and price:
                products.append({
                    "name": name.text,
                    "price": price.text,
                    "link": f"https://shope.ee/{SHOPEE_AFFILIATE_ID}"
                })
        except AttributeError:
            continue
    
    return products

# ฟังก์ชันใช้ OpenAI ตอบลูกค้า
def chat_with_ai(user_message):
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": "gpt-4",
                "messages": [
                    {"role": "system", "content": "คุณเป็นแชทบอทแนะนำสินค้าราคาถูก"},
                    {"role": "user", "content": user_message}
                ]
            }
        )

        response_data = response.json()
        return response_data.get("choices", [{}])[0].get("message", {}).get("content", "ขออภัย ฉันไม่สามารถตอบคำถามนี้ได้")
    except Exception as e:
        logging.error(f"⚠️ Error occurred while communicating with OpenAI: {str(e)}")
        return "⚠️ ข้อผิดพลาดในการเชื่อมต่อ AI"

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

    logging.debug(f"📨 Sending payload to LINE: {json.dumps(payload, indent=2)}")
    print(f"📨 Sending to LINE: {json.dumps(payload, indent=2)}")

    response = requests.post(LINE_REPLY_URL, headers=headers, json=payload)

    if response.status_code == 200:
        logging.info("✅ Message sent to LINE successfully!")
        print("✅ Message sent to LINE successfully!")
    else:
        logging.error(f"⚠️ Error sending message: {response.text}")
        print(f"⚠️ Error sending message: {response.text}")

    return response.status_code

# Route ตรวจสอบเซิร์ฟเวอร์
@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Server is running!"}), 200

# LINE Webhook
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    logging.debug(f"📥 Received request: {json.dumps(data, indent=2)}")

    if "events" not in data or not data["events"]:
        return jsonify({"error": "Invalid request"}), 400

    event = data["events"][0]
    user_message = event.get("message", {}).get("text", "")
    reply_token = event.get("replyToken", "")

    if not user_message or not reply_token:
        logging.warning("⚠️ No message received in webhook event")
        return jsonify({"error": "No message received"}), 400

    ai_reply = chat_with_ai(user_message)

    # ส่งข้อความตอบกลับไปยัง LINE
    status = reply_to_line(reply_token, ai_reply)

    return jsonify({"status": status, "reply": ai_reply})

if __name__ == "__main__":
    app.run(port=5000)
