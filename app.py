import os
import time
import hmac
import hashlib
import requests
import urllib.parse
import json
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# ✅ โหลด Environment Variables (ใช้เฉพาะใน Local)
if os.getenv("RENDER") is None:
    load_dotenv()

# ✅ ตั้งค่า API Credentials
LINE_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LAZADA_APP_KEY = os.getenv("LAZADA_APP_KEY")
LAZADA_APP_SECRET = os.getenv("LAZADA_APP_SECRET")
LAZADA_USER_TOKEN = os.getenv("LAZADA_USER_TOKEN")
LAZADA_AFFILIATE_ID = os.getenv("LAZADA_AFFILIATE_ID")

# ✅ ตั้งค่า Flask App
app = Flask(__name__)

# ✅ ฟังก์ชัน Debug Log
def debug_log(message):
    print(f"🛠 DEBUG: {message}")

# ✅ ฟังก์ชันสร้าง Signature สำหรับ Lazada API
def generate_signature(params):
    sorted_params = sorted(params.items(), key=lambda x: x[0])
    base_string = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in sorted_params)
    signature = hmac.new(
        LAZADA_APP_SECRET.encode(), base_string.encode(), hashlib.sha256
    ).hexdigest().upper()
    return signature

# ✅ ค้นหาสินค้าที่ขายดีที่สุดจาก Lazada
def get_best_selling_lazada(keyword):
    endpoint = "https://api.lazada.co.th/rest/products/search"
    params = {
        "app_key": LAZADA_APP_KEY,
        "timestamp": str(int(time.time() * 1000)),
        "sign_method": "sha256",
        "access_token": LAZADA_USER_TOKEN,
        "format": "JSON",
        "v": "1.0",
        "q": keyword,
        "sort_by": "sales_volume"
    }

    params["sign"] = generate_signature(params)
    response = requests.get(endpoint, params=params).json()
    
    debug_log(f"Lazada Search Response: {response}")

    if "data" in response and "products" in response["data"]:
        best_product = sorted(response["data"]["products"], key=lambda x: x["sales"], reverse=True)[0]
        return best_product["url"], best_product["name"]

    return None, None

# ✅ สร้างลิงก์ Affiliate จาก Lazada API
def generate_lazada_affiliate_link(product_url):
    endpoint = "https://api.lazada.co.th/rest/affiliate/link/generate"
    params = {
        "app_key": LAZADA_APP_KEY,
        "timestamp": str(int(time.time() * 1000)),
        "sign_method": "sha256",
        "access_token": LAZADA_USER_TOKEN,
        "format": "JSON",
        "v": "1.0",
        "tracking_id": LAZADA_AFFILIATE_ID,
        "url": product_url
    }

    params["sign"] = generate_signature(params)
    response = requests.get(endpoint, params=params).json()
    
    debug_log(f"Lazada Affiliate Response: {response}")

    if "data" in response and "aff_link" in response["data"]:
        return response["data"]["aff_link"]

    return None

# ✅ Webhook API สำหรับรับข้อความจาก LINE และส่งลิงก์สินค้า
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        debug_log(f"Received Data: {data}")

        if not data or "events" not in data:
            return jsonify({"error": "❌ ไม่มีข้อมูลที่ส่งมา"}), 400

        event = data["events"][0]

        if event.get("type") == "message" and event["message"].get("type") == "text":
            user_id = event["source"]["userId"]
            text = event["message"]["text"]
            reply_token = event["replyToken"]

            product_url, product_name = get_best_selling_lazada(text)

            if not product_url:
                response_text = f"❌ ไม่พบสินค้าที่ตรงกับ '{text}'"
            else:
                lazada_link = generate_lazada_affiliate_link(product_url)
                if not lazada_link:
                    response_text = f"❌ ไม่สามารถสร้างลิงก์ Affiliate สำหรับ '{text}'"
                else:
                    response_text = f"🔎 ค้นหาสินค้าเกี่ยวกับ: {text}\n\n🛍 Lazada: {lazada_link}"

            send_line_message(reply_token, response_text)

        return jsonify({"status": "ok"})

    except Exception as e:
        debug_log(f"❌ Error: {str(e)}")
        return jsonify({"error": f"❌ Internal Server Error: {str(e)}"}), 500

# ✅ ฟังก์ชันส่งข้อความไปที่ LINE
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
    debug_log(f"LINE API Response: {response.json()}")

# ✅ ให้ Flask ใช้พอร์ตที่ถูกต้อง
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug_log(f"✅ Starting Flask on port {port}...")
    app.run(host="0.0.0.0", port=port)
