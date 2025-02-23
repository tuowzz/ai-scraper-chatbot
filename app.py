import os
import time
import hmac
import hashlib
import requests
import urllib.parse
from flask import Flask, request, jsonify

app = Flask(__name__)

# ✅ โหลด API Keys
LAZADA_APP_KEY = os.getenv("LAZADA_APP_KEY")
LAZADA_APP_SECRET = os.getenv("LAZADA_APP_SECRET")
LAZADA_USER_TOKEN = os.getenv("LAZADA_USER_TOKEN")
LAZADA_REFRESH_TOKEN = os.getenv("LAZADA_REFRESH_TOKEN")  # เพิ่ม Refresh Token
LAZADA_AFFILIATE_ID = os.getenv("LAZADA_AFFILIATE_ID")

# ✅ ฟังก์ชันอัปเดต Access Token อัตโนมัติ
def refresh_access_token():
    global LAZADA_USER_TOKEN, LAZADA_REFRESH_TOKEN
    url = "https://auth.lazada.com/rest"
    
    params = {
        "app_key": LAZADA_APP_KEY,
        "timestamp": str(int(time.time() * 1000)),
        "sign_method": "sha256",
        "method": "accessToken.refresh",
        "refresh_token": LAZADA_REFRESH_TOKEN
    }

    # 🔹 สร้าง Signature
    sorted_params = sorted(params.items(), key=lambda x: x[0])
    base_string = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in sorted_params)
    signature = hmac.new(
        LAZADA_APP_SECRET.encode(), base_string.encode(), hashlib.sha256
    ).hexdigest().upper()

    params["sign"] = signature
    response = requests.post(url, params=params).json()

    if "access_token" in response:
        LAZADA_USER_TOKEN = response["access_token"]
        LAZADA_REFRESH_TOKEN = response["refresh_token"]
        os.environ["LAZADA_USER_TOKEN"] = LAZADA_USER_TOKEN
        os.environ["LAZADA_REFRESH_TOKEN"] = LAZADA_REFRESH_TOKEN
        print("✅ Access Token อัปเดตเรียบร้อย!")
    else:
        print("❌ ไม่สามารถอัปเดต Access Token ได้", response)

# ✅ ฟังก์ชันค้นหาสินค้าที่ขายดีที่สุด
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

    # 🔹 สร้าง Signature
    sorted_params = sorted(params.items(), key=lambda x: x[0])
    base_string = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in sorted_params)
    signature = hmac.new(
        LAZADA_APP_SECRET.encode(), base_string.encode(), hashlib.sha256
    ).hexdigest().upper()

    params["sign"] = signature
    url = "https://api.lazada.co.th/rest?" + "&".join(f"{k}={v}" for k, v in params.items())

    response = requests.get(url).json()
    
    if "data" in response and "products" in response["data"]:
        best_product = response["data"]["products"][0]  # ✅ ดึงสินค้าที่ขายดีที่สุด
        product_id = best_product["product_id"]
        return product_id, best_product["name"]
    
    return None, None

# ✅ ฟังก์ชันสร้างลิงก์ Affiliate
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

    # 🔹 สร้าง Signature
    sorted_params = sorted(params.items(), key=lambda x: x[0])
    base_string = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in sorted_params)
    signature = hmac.new(
        LAZADA_APP_SECRET.encode(), base_string.encode(), hashlib.sha256
    ).hexdigest().upper()

    params["sign"] = signature
    url = "https://api.lazada.co.th/rest?" + "&".join(f"{k}={v}" for k, v in params.items())

    response = requests.get(url).json()
    
    if "data" in response and "aff_link" in response["data"]:
        return response["data"]["aff_link"]
    
    return None

# ✅ Webhook API
@app.route("/search_lazada", methods=["POST"])
def search_lazada():
    data = request.get_json()
    keyword = data.get("keyword")

    if not keyword:
        return jsonify({"error": "กรุณาระบุคำค้นหา"}), 400

    # ✅ ตรวจสอบ Access Token
    if not LAZADA_USER_TOKEN:
        print("🔄 กำลังอัปเดต Access Token...")
        refresh_access_token()

    # ✅ ค้นหาสินค้าที่ขายดีที่สุด
    product_id, product_name = get_best_selling_lazada(keyword)

    if not product_id:
        return jsonify({"error": "ไม่พบสินค้าที่ตรงกับคำค้นหา"}), 404

    # ✅ สร้างลิงก์ Affiliate
    lazada_link = generate_lazada_affiliate_link(product_id)

    if not lazada_link:
        return jsonify({"error": "ไม่สามารถสร้างลิงก์ Affiliate ได้"}), 500

    return jsonify({
        "keyword": keyword,
        "product_name": product_name,
        "affiliate_link": lazada_link
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
