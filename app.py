import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return "AI Scraper Chatbot is running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
