from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "AI Scraper Chatbot is running!"

if name == "__main__":
    app.run(host="0.0.0.0", port=5000)
