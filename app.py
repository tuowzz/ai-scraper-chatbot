import requests
import openai
from flask import Flask, request, jsonify
from bs4 import BeautifulSoup
import json
import os

app = Flask(__name__)

# ตั้งค่า API Key จาก Environment Variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
SHOPEE_AFFILIATE_ID = os.getenv("SHOPEE_AFFILIATE_ID", "9A9ZBqQZk5")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_REPLY_URL = "https://api.line.me/v2/bot/message/reply"

if not OPENAI_API_KEY:
    print("⚠️ OPENAI_API_KEY is missing. Please set it in environment variables.")
    sys.exit(1)
if not LINE_CHANNEL_ACCESS_TOKEN:
    print("⚠️ LINE_CHANNEL_ACCESS_TOKEN is missing. Please set it in environment variables.")
    sys.exit(1)

# ฟังก์ชันดึงข้อมูลจาก Shopee
def scrape_shopee(keyword):
    url = f"https://shopee.co.th/search?keyword={keyword}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"⚠️ Failed to fetch data from Shopee. Status code: {response.status_code}")
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
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "คุณเป็นแชทบอทแนะนำสินค้าราคาถูก"},
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
    
    ai_reply = chat_with_ai(user_message)
    
    # ส่งข้อความตอบกลับไปยัง LINE
    status = reply_to_line(reply_token, ai_reply)
    
    return jsonify({"status": status, "reply": ai_reply})

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Server is running"})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
