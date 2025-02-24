import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# ✅ โหลด LINE Access Token
LINE_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

# ✅ ฟังก์ชัน Debug Log
def debug_log(message):
    print(f"🛠 DEBUG: {message}")

# ✅ ฟังก์ชันส่งข้อความกลับไปที่ LINE
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
    return response.status_code

# ✅ Webhook รองรับเฉพาะ POST เท่านั้น
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        debug_log(f"Received Data: {data}")  # Debug log

        # ✅ เช็คว่ามี events หรือไม่
        if not data or "events" not in data or len(data["events"]) == 0:
            debug_log("⚠️ ไม่มี events ใน request")
            return jsonify({"error": "❌ ไม่มี events ใน request"}), 400

        event = data["events"][0]  # ✅ ดึง Event แรก (ถ้ามี)

        # ✅ เช็คว่าเป็นข้อความหรือไม่
        if "message" not in event or "text" not in event["message"]:
            debug_log("⚠️ ไม่ใช่ข้อความที่สามารถอ่านได้")
            return jsonify({"error": "❌ ไม่ใช่ข้อความที่สามารถอ่านได้"}), 400

        text = event["message"]["text"]
        reply_token = event["replyToken"]

        # ✅ ตอบกลับข้อความที่ได้รับ
        response_text = f"🔄 คุณพิมพ์ว่า: {text}"
        status_code = send_line_message(reply_token, response_text)

        return jsonify({"status": "✅ ส่งข้อความกลับสำเร็จ"}), status_code

    except Exception as e:
        debug_log(f"❌ Error: {str(e)}")
        return jsonify({"error": f"❌ Internal Server Error: {str(e)}"}), 500

# ✅ ตรวจสอบว่าเซิร์ฟเวอร์รันอยู่ (ใช้ GET)
@app.route("/", methods=["GET"])
def home():
    return "✅ LINE Webhook ทำงานปกติ", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug_log(f"✅ LINE Webhook รันที่พอร์ต {port}...")
    app.run(host="0.0.0.0", port=port)
