import os
import requests
from flask import Flask, request, jsonify

from dotenv import load_dotenv  # โหลดค่าจาก .env
load_dotenv()

app = Flask(__name__)

# ✅ โหลดค่า API จาก .env
LINE_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

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
    return response.status_code

# ✅ Webhook สำหรับรับข้อความจาก LINE
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        print(f"🛠 DEBUG: Received Data: {data}")

        if not data or "events" not in data or len(data["events"]) == 0:
            return jsonify({"error": "❌ ไม่มี events ใน request"}), 400

        event = data["events"][0]
        text = event["message"]["text"]
        reply_token = event["replyToken"]

        response_text = f"🔄 คุณพิมพ์ว่า: {text}"
        send_line_message(reply_token, response_text)

        return jsonify({"status": "✅ ส่งข้อความกลับสำเร็จ"}), 200

    except Exception as e:
        return jsonify({"error": f"❌ Internal Server Error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
