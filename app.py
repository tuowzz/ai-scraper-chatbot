import os
import time
import hmac
import hashlib
import requests
import urllib.parse
from flask import Flask, request, jsonify

app = Flask(__name__)

# ✅ โหลด API Keys
LINE_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LAZADA_APP_KEY = os.getenv("LAZADA_APP_KEY")
LAZADA_APP_SECRET = os.getenv("LAZADA_APP_SECRET")
LAZADA_USER_TOKEN = os.getenv("LAZADA_USER_TOKEN")
LAZADA_AFFILIATE_ID = os.getenv("LAZADA_AFFILIATE_ID")

LINE_REPLY_URL = "https://api.line.me/v2/bot/message/reply"

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

# ✅ ฟังก์ชันค้นหาสินค้าขายดีบน Lazada
def get_best_selling_lazada(keyword):
    endpoint = "https://api.lazada.co.th/rest/products/search"  # เปลี่ยนให้ตรงกับ API ใหม่
    params = {
        "app_key": LAZADA_APP_KEY,
        "timestamp": str(int(time.time() * 1000)),
        "sign_method": "sha256",
        "access_token": LAZADA_USER_TOKEN,
        "format": "JSON",
        "v": "1.0",
        "q": keyword,  # ✅ ใช้คำค้นหาที่ส่งมา
        "sort_by": "sales_volume"  # 🔥 เรียงลำดับตามยอดขายสูงสุด
    }

    params["sign"] = generate_signature(params)
    debug_log(f"Request Params: {params}")  # เพิ่ม Debug Log

    response = requests.get(endpoint, params=params).json()
    
    debug_log(f"Lazada Search Response: {response}")

    if "data" in response and "products" in response["data"]:
        best_product = sorted(response["data"]["products"], key=lambda x: x["sales"], reverse=True)[0]
        product_url = best_product["url"]
        product_name = best_product["name"]
        return product_url, product_name

    return None, None

# ✅ ฟังก์ชันสร้างลิงก์ Affiliate สำหรับ Lazada
def generate_lazada_affiliate_link(product_url):
    endpoint = "https://api.lazada.co.th/rest/affiliate/link/generate"  # เปลี่ยนให้ตรงกับ API ใหม่
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
    debug_log(f"Affiliate Link Params: {params}")  # เพิ่ม Debug Log

    response = requests.get(endpoint, params=params).json()
    
    debug_log(f"Lazada Affiliate Response: {response}")

    if "data" in response and "aff_link" in response["data"]:
        return response["data"]["aff_link"]

    return None

# ✅ ฟังก์ชันส่งข้อความกลับไปยัง LINE
def send_line_message(reply_token, text):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
    }
    payload = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": text}]
    }

    response = requests.post(LINE_REPLY_URL, headers=headers, json=payload)
    debug_log(f"LINE API Response: {response.json()}")

# ✅ Webhook API ที่รับคำค้นหาและสร้างลิงก์ Lazada
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        debug_log(f"Received Data: {data}")

        if not data or "events" not in data:
            return jsonify({"error": "❌ ไม่มีข้อมูลที่ส่งมา"}), 400

        event = data["events"][0]
        if "message" not in event or "text" not in event["message"]:
            return jsonify({"error": "❌ ข้อความไม่ถูกต้อง"}), 400

        keyword = event["message"]["text"]
        reply_token = event["replyToken"]

        if not keyword:
            return jsonify({"error": "❌ กรุณาระบุคำค้นหา"}), 400

        product_url, product_name = get_best_selling_lazada(keyword)

        if not product_url:
            send_line_message(reply_token, f"❌ ไม่พบสินค้าสำหรับ: {keyword}")
            return jsonify({"error": "❌ ไม่พบสินค้าที่ตรงกับคำค้นหา"}), 404

        lazada_link = generate_lazada_affiliate_link(product_url)

        if not lazada_link:
            send_line_message(reply_token, "❌ ไม่สามารถสร้างลิงก์ Affiliate ได้")
            return jsonify({"error": "❌ ไม่สามารถสร้างลิงก์ Affiliate ได้"}), 500

        response_text = (
            f"🔎 ค้นหาสินค้าเกี่ยวกับ: {keyword}\n\n"
            f"🛍 Lazada: {lazada_link}\n\n"
            f"🔥 โปรโมชั่นมาแรง! รีบสั่งซื้อตอนนี้ก่อนสินค้าหมด 🔥"
        )

        send_line_message(reply_token, response_text)
        return jsonify({"status": "✅ สำเร็จ"})

    except Exception as e:
        debug_log(f"❌ Error: {str(e)}")
        return jsonify({"error": f"❌ Internal Server Error: {str(e)}"}), 500

# ✅ ให้ Flask ใช้พอร์ตที่ถูกต้อง
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug_log(f"✅ Starting Flask on port {port}...")
    app.run(host="0.0.0.0", port=port)
