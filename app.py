import os
import time
import hmac
import hashlib
import requests
import urllib.parse
from flask import Flask, request, jsonify

app = Flask(__name__)

# ✅ โหลด API Keys จาก Environment Variables
LAZADA_APP_KEY = os.getenv("LAZADA_APP_KEY")
LAZADA_APP_SECRET = os.getenv("LAZADA_APP_SECRET")
LAZADA_USER_TOKEN = os.getenv("LAZADA_USER_TOKEN")
LAZADA_AFFILIATE_ID = os.getenv("LAZADA_AFFILIATE_ID")
LINE_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

# ✅ ฟังก์ชันสร้าง Signature สำหรับ Lazada API
def generate_signature(params):
    sorted_params = sorted(params.items(), key=lambda x: x[0])
    base_string = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in sorted_params)
    signature = hmac.new(
        LAZADA_APP_SECRET.encode(), base_string.encode(), hashlib.sha256
    ).hexdigest().upper()
    return signature

# ✅ ฟังก์ชันค้นหาสินค้าขายดีบน Lazada
def get_best_selling_lazada(keyword):
    params = {
        "app_key": LAZADA_APP_KEY,
        "timestamp": str(int(time.time() * 1000)),
        "sign_method": "sha256",
        "access_token": LAZADA_USER_TOKEN,
        "method": "lazada.product.search",
        "format": "JSON",
        "v": "1.0",
        "q": keyword,
        "sort_by": "sales_volume"
    }
    
    params["sign"] = generate_signature(params)
    url = "https://api.lazada.co.th/rest?" + "&".join(f"{k}={v}" for k, v in params.items())

    response = requests.get(url).json()
    
    if "data" in response and "products" in response["data"]:
        best_product = response["data"]["products"][0]
        product_id = best_product["product_id"]
        return product_id, best_product["name"]
    
    return None, None

# ✅ ฟังก์ชันสร้างลิงก์ Affiliate สำหรับ Lazada
def generate_lazada_affiliate_link(product_id):
    params = {
        "app_key": LAZADA_APP_KEY,
        "timestamp": str(int(time.time() * 1000)),
        "sign_method": "sha256",
        "access_token": LAZADA_USER_TOKEN,
        "method": "lazada.generate.afflink",
        "format": "JSON",
        "v": "1.0",
        "tracking_id": LAZADA_AFFILIATE_ID,
        "url": f"https://www.lazada.co.th/products/{product_id}.html"
    }

    params["sign"] = generate_signature(params)
    url = "https://api.lazada.co.th/rest?" + "&".join(f"{k}={v}" for k, v in params.items())

    response = requests.get(url).json()
    
    if "data" in response and "aff_link" in response["data"]:
        return response["data"]["aff_link"]
    
    return None

# ✅ ฟังก์ชันตอบกลับไปยัง LINE Webhook
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
    requests.post(url, headers=headers, json=payload)

# ✅ Webhook API ค้นหาสินค้า & ส่งลิงก์ Lazada
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    events = data.get("events", [])

    for event in events:
        if event.get("type") == "message" and event["message"].get("type") == "text":
            user_id = event["source"]["userId"]
            text = event["message"]["text"]
            reply_token = event["replyToken"]

            # ✅ ค้นหาสินค้า
            product_id, product_name = get_best_selling_lazada(text)

            if not product_id:
                response_text = "❌ ไม่พบสินค้าที่คุณค้นหา"
            else:
                # ✅ สร้างลิงก์ Affiliate
                lazada_link = generate_lazada_affiliate_link(product_id)
                if not lazada_link:
                    response_text = "❌ ไม่สามารถสร้างลิงก์ Lazada ได้"
                else:
                    response_text = (f"🔎 ค้นหาสินค้าเกี่ยวกับ: {text}\n\n"
                                     f"🛍 Lazada: \n➡️ {lazada_link}\n\n"
                                     f"🔥 โปรโมชั่นมาแรง! รีบสั่งซื้อตอนนี้ก่อนสินค้าหมด 🔥")

            send_line_message(reply_token, response_text)

    return jsonify({"status": "ok"})

# ✅ เรียกใช้งาน Flask บน Render หรือ Google Cloud
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
