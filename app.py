import requests
from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)

# ตั้งค่า Affiliate ID และ Token
SHOPEE_AFFILIATE_ID = "15384150058"  # ใส่ Affiliate ID ของ Shopee
LAZADA_AFFILIATE_ID = "272261049"  # ใส่ Affiliate ID ของ Lazada
TIKTOK_AFFILIATE_ID = "7494437765104241417"  # ใส่ Affiliate ID ของ TikTok
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
BITLY_ACCESS_TOKEN = os.getenv("BITLY_ACCESS_TOKEN", "")

LINE_REPLY_URL = "https://api.line.me/v2/bot/message/reply"

if not LINE_CHANNEL_ACCESS_TOKEN:
    print("⚠️ LINE_CHANNEL_ACCESS_TOKEN is missing. Please set it in environment variables.")
    exit(1)

# ฟังก์ชันสร้างลิงก์ Shopee (ใช้ Universal Link ที่กดได้)
def get_shopee_search_link(keyword):
    base_url = "https://shopee.co.th/search"
    full_link = f"{base_url}?keyword={keyword}&af_id={SHOPEE_AFFILIATE_ID}"
    return shorten_url(full_link)

# ฟังก์ชันสร้างลิงก์ Lazada
def get_lazada_search_link(keyword):
    base_url = "https://www.lazada.co.th/catalog/"
    full_link = f"{base_url}?q={keyword}&sub_aff_id={LAZADA_AFFILIATE_ID}"
    return shorten_url(full_link)

# ฟังก์ชันสร้างลิงก์ TikTok Shop
def get_tiktok_search_link(keyword):
    base_url = "https://www.tiktok.com/shop"
    full_link = f"{base_url}?q={keyword}&cid={TIKTOK_AFFILIATE_ID}"
    return shorten_url(full_link)

# ฟังก์ชันย่อลิงก์ด้วย Bitly
def shorten_url(long_url):
    if not BITLY_ACCESS_TOKEN:
        return long_url  # ถ้าไม่มี Bitly Token ให้ใช้ลิงก์ยาว
    try:
        headers = {"Authorization": f"Bearer {BITLY_ACCESS_TOKEN}", "Content-Type": "application/json"}
        data = {"long_url": long_url}
        response = requests.post("https://api-ssl.bitly.com/v4/shorten", headers=headers, json=data)
        if response.status_code == 200:
            return response.json().get("link", long_url)
        else:
            return long_url
    except Exception as e:
        return long_url

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

    # สร้างลิงก์ Shopee, Lazada และ TikTok
    shopee_link = get_shopee_search_link(user_message)
    lazada_link = get_lazada_search_link(user_message)
    tiktok_link = get_tiktok_search_link(user_message)
    
    response_message = (
        f"🔎 ค้นหาสินค้าเกี่ยวกับ: {user_message}\n\n"
        f"🛒 Shopee: {shopee_link}\n\n"
        f"🛍 Lazada: {lazada_link}\n\n"
        f"🎵 TikTok Shop: {tiktok_link}"
    )

    # ส่งข้อความตอบกลับไปยัง LINE
    status = reply_to_line(reply_token, response_message)

    return jsonify({"status": status, "reply": response_message})

if __name__ == "__main__":
    app.run(port=5000)
