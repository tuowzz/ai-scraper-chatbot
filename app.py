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

# ✅ ฟังก์ชันค้นหาสินค้าที่ขายดีที่สุดใน Lazada
def get_best_selling_lazada(keyword):
    try:
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
        print("🔹 API Response (Search):", response)  # ✅ Debug Log

        if "code" in response and response["code"] != "0":
            return None, f"⚠️ Lazada API Error: {response.get('message', 'Unknown Error')}"

        if "data" in response and "products" in response["data"]:
            best_product = response["data"]["products"][0]
            product_id = best_product["product_id"]
            return product_id, best_product["name"]

        return None, "❌ ไม่พบสินค้าที่ขายดีที่สุด"
    
    except Exception as e:
        return None, f"⚠️ Error: {str(e)}"

# ✅ ฟังก์ชันสร้างลิงก์ Affiliate จาก Lazada API
def generate_lazada_affiliate_link(product_id):
    try:
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
        print("🔹 API Response (Affiliate Link):", response)  # ✅ Debug Log

        if "data" in response and "aff_link" in response["data"]:
            return response["data"]["aff_link"]

        return None
    
    except Exception as e:
        return None

# ✅ Webhook API ที่รับคำค้นหาและสร้างลิงก์ Lazada
@app.route("/search_lazada", methods=["POST"])
def search_lazada():
    data = request.get_json()
    keyword = data.get("keyword")

    if not keyword:
        return jsonify({"error": "⚠️ กรุณาระบุคำค้นหา"}), 400

    # ✅ ค้นหาสินค้ายอดนิยม
    product_id, product_name_or_error = get_best_selling_lazada(keyword)

    if not product_id:
        return jsonify({"error": product_name_or_error}), 404

    # ✅ สร้างลิงก์ Lazada Affiliate
    lazada_link = generate_lazada_affiliate_link(product_id)

    if not lazada_link:
        return jsonify({"error": "⚠️ ไม่สามารถสร้างลิงก์ Affiliate ได้"}), 500

    return jsonify({
        "keyword": keyword,
        "product_name": product_name_or_error,
        "affiliate_link": lazada_link
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
