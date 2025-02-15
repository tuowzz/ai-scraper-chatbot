from flask import Flask, request, jsonify
from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "AI Scraper Chatbot is running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    if not data or "events" not in data:
        return jsonify({"error": "Invalid request"}), 400
    
    # อ่านข้อความจาก LINE
    event = data["events"][0]
    user_message = event.get("message", {}).get("text", "")
    reply_token = event.get("replyToken", "")

    if not user_message or not reply_token:
        return jsonify({"error": "No message received"}), 400

    # ใช้ OpenAI ตอบกลับข้อความ
    ai_reply = chat_with_ai(user_message)

    # ส่งข้อความกลับไป LINE
    status = reply_to_line(reply_token, ai_reply)

    return jsonify({"status": status, "reply": ai_reply}), 200
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json  # ใช้ request.json เพื่อดึงข้อมูล
    if "events" not in data or not data["events"]:
        return jsonify({"error": "Invalid request"}), 400
