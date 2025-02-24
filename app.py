import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# ✅ กำหนดค่า API จาก Environment Variables
LINE_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

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
    return response.json()

# ✅ Webhook สำหรับรับข้อความจาก LINE
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print(f"🛠 DEBUG: Received Data: {data}")  # ดูข้อมูลที่ได้รับจาก LINE

    if not data or "events" not in data:
        return jsonify({"error": "❌ ไม่มีข้อมูลที่ส่งมา"}), 400

    event = data["events"][0]
    if "message" not in event or "text" not in event["message"]:
        return jsonify({"error": "❌ ข้อความไม่ถูกต้อง"}), 400

    text = event["message"]["text"]
    reply_token = event["replyToken"]

    # ✅ ตอบกลับข้อความอัตโนมัติ
    response_text = f"🔄 คุณพิมพ์ว่า: {text}"
    send_line_message(reply_token, response_text)

    return jsonify({"status": "✅ ส่งข้อความกลับสำเร็จ"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"✅ LINE Webhook กำลังรันที่พอร์ต {port}...")
    app.run(host="0.0.0.0", port=port)
