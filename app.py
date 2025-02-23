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

# ✅ ฟังก์ชันค้นหาสินค้า Lazada
def get_best_selling_lazada(keyword):
    params = {
        "app_key": LAZADA_APP_KEY,
        "timestamp": str(int(time.time() * 1000)),
        "sign_method": "sha256",
        "access_token": LAZADA_USER_TOKEN,
        "method": "lazada.seller.product.get",
        "format": "JSON",
        "v": "1.0",
        "search": keyword
    }

    params["sign"] = generate_signature(params)
    url = "https://api.lazada.co.th/rest?" + "&".join(f"{k}={v}" for k, v in params.items())

    response = requests.get(url).json()
    debug_log(f"Lazada Search Response: {response}")

    if "data" in response and "products" in response["data"]:
        best_product = sorted(response["data"]["products"], key=lambda x: x["sales"], reverse=True)[0]
        product_id = best_product["item_id"]
        return product_id, best_product["name"]

    return None, None

# ✅ ฟังก์ชันสร้างลิงก์ Affiliate
def generate_lazada_affiliate_link(product_id):
    params = {
        "app_key": LAZADA_APP_KEY,
        "timestamp": str(int(time.time() * 1000)),
        "sign_method": "sha256",
        "access_token": LAZADA_USER_TOKEN,
        "method": "lazada.affiliate.generateLink",
        "format": "JSON",
        "v": "1.0",
        "tracking_id": LAZADA_AFFILIATE_ID,
        "url": f"https://www.lazada.co.th/products/{product_id}.html"
    }

    params["sign"] = generate_signature(params)
    url = "https://api.lazada.co.th/rest?" + "&".join(f"{k}={v}" for k, v in params.items())

    response = requests.get(url).json()
    debug_log(f"Lazada Affiliate Response: {response}")

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

        product_id, product_name = get_best_selling_lazada(keyword)

        if not product_id:
            return jsonify({"error": "❌ ไม่พบสินค้าที่ตรงกับคำค้นหา"}), 404

        lazada_link = generate_lazada_affiliate_link(product_id)

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
