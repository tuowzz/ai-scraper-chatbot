import os
import time
import hmac
import hashlib
import requests
import urllib.parse
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

# ✅ โหลด API Keys จาก Environment Variables
LAZADA_APP_KEY = os.getenv("LAZADA_APP_KEY", "132211")
LAZADA_APP_SECRET = os.getenv("LAZADA_APP_SECRET", "Xgs5j7N6SNvuVdHo9d6ybwd3LhVvaHVY")
LAZADA_ACCESS_TOKEN = os.getenv("LAZADA_ACCESS_TOKEN")  # Access Token ต้องอัปเดตทุก 30 นาที - 1 ชั่วโมง
LAZADA_REFRESH_TOKEN = os.getenv("LAZADA_REFRESH_TOKEN")  # ใช้ขอ Access Token ใหม่เมื่อหมดอายุ
LAZADA_AFFILIATE_ID = os.getenv("LAZADA_AFFILIATE_ID")

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

# ✅ ฟังก์ชันรีเฟรช Access Token อัตโนมัติ
def refresh_access_token():
    global LAZADA_ACCESS_TOKEN, LAZADA_REFRESH_TOKEN
    endpoint = "https://auth.lazada.com/rest/token"
    params = {
        "app_key": LAZADA_APP_KEY,
        "timestamp": str(int(time.time() * 1000)),
        "sign_method": "sha256",
        "grant_type": "refresh_token",
        "refresh_token": LAZADA_REFRESH_TOKEN
    }
    params["sign"] = generate_signature(params)

    response = requests.post(endpoint, data=params).json()
    debug_log(f"Lazada Token Refresh Response: {response}")

    if "access_token" in response:
        LAZADA_ACCESS_TOKEN = response["access_token"]
        LAZADA_REFRESH_TOKEN = response["refresh_token"]
        return True
    return False

# ✅ ฟังก์ชันค้นหาสินค้าขายดีบน Lazada
def get_best_selling_lazada(keyword):
    endpoint = "https://api.lazada.co.th/rest/products/search"
    params = {
        "app_key": LAZADA_APP_KEY,
        "timestamp": str(int(time.time() * 1000)),
        "sign_method": "sha256",
        "access_token": LAZADA_ACCESS_TOKEN,
        "format": "JSON",
        "v": "1.0",
        "q": keyword,
        "sort_by": "sales_volume"
    }
    params["sign"] = generate_signature(params)

    response = requests.get(endpoint, params=params).json()
    debug_log(f"Lazada Search Response: {response}")

    if "code" in response and response["code"] == "AccessTokenExpired":
        if refresh_access_token():
            return get_best_selling_lazada(keyword)  # 🔁 ลองใหม่หลังจากรีเฟรช Token
        return None, None

    if "data" in response and "products" in response["data"]:
        best_product = sorted(response["data"]["products"], key=lambda x: x["sales"], reverse=True)[0]
        product_url = best_product["url"]
        product_name = best_product["name"]
        return product_url, product_name

    return None, None

# ✅ ฟังก์ชันสร้างลิงก์ Affiliate สำหรับ Lazada
def generate_lazada_affiliate_link(product_url):
    endpoint = "https://api.lazada.co.th/rest/affiliate/link/generate"
    params = {
        "app_key": LAZADA_APP_KEY,
        "timestamp": str(int(time.time() * 1000)),
        "sign_method": "sha256",
        "access_token": LAZADA_ACCESS_TOKEN,
        "format": "JSON",
        "v": "1.0",
        "tracking_id": LAZADA_AFFILIATE_ID,
        "url": product_url
    }
    params["sign"] = generate_signature(params)

    response = requests.get(endpoint, params=params).json()
    debug_log(f"Lazada Affiliate Response: {response}")

    if "code" in response and response["code"] == "AccessTokenExpired":
        if refresh_access_token():
            return generate_lazada_affiliate_link(product_url)  # 🔁 ลองใหม่หลังจากรีเฟรช Token
        return None

    if "data" in response and "aff_link" in response["data"]:
        return response["data"]["aff_link"]

    return None

# ✅ Webhook API ที่รับคำค้นหาและสร้างลิงก์ Lazada
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        debug_log(f"Received Data: {data}")

        if not data:
            return jsonify({"error": "❌ ไม่มีข้อมูลที่ส่งมา"}), 400

        keyword = data.get("keyword", "default_keyword")

        if not keyword:
            return jsonify({"error": "❌ กรุณาระบุคำค้นหา"}), 400

        product_url, product_name = get_best_selling_lazada(keyword)

        if not product_url:
            return jsonify({"error": "❌ ไม่พบสินค้าที่ตรงกับคำค้นหา"}), 404

        lazada_link = generate_lazada_affiliate_link(product_url)

        if not lazada_link:
            return jsonify({"error": "❌ ไม่สามารถสร้างลิงก์ Affiliate ได้"}), 500

        return jsonify({
            "keyword": keyword,
            "product_name": product_name,
            "affiliate_link": lazada_link
        })

    except Exception as e:
        debug_log(f"❌ Error: {str(e)}")
        return jsonify({"error": f"❌ Internal Server Error: {str(e)}"}), 500

# ✅ ให้ Flask ใช้พอร์ตที่ถูกต้อง
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug_log(f"✅ Starting Flask on port {port}...")
    app.run(host="0.0.0.0", port=port)
