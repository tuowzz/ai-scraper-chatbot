import requests
import random
import re
from bs4 import BeautifulSoup

# Shopee: ค้นหาสินค้า → สุ่ม 1 รายการ
def get_shopee_product_link(keyword):
    search_url = f"https://shopee.co.th/search?keyword={keyword}"
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    product_links = []
    for a_tag in soup.find_all("a", href=True):
        if re.search(r"/product/\d+/\d+", a_tag["href"]):
            product_links.append("https://shopee.co.th" + a_tag["href"])

    return random.choice(product_links) if product_links else search_url

# Lazada: ค้นหาสินค้า → สุ่ม 1 รายการ
def get_lazada_product_link(keyword):
    search_url = f"https://www.lazada.co.th/catalog/?q={keyword}"
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    product_links = []
    for a_tag in soup.find_all("a", href=True):
        if re.search(r"/products/.*?-\d+.html", a_tag["href"]):
            product_links.append("https:" + a_tag["href"])

    return random.choice(product_links) if product_links else search_url

# ตัวอย่างการใช้งาน
keyword = "ลิปแมทเนื้อดี"
shopee_link = get_shopee_product_link(keyword)
lazada_link = get_lazada_product_link(keyword)

print(f"🔎 ค้นหาสินค้าเกี่ยวกับ: {keyword}\n")
print(f"🛒 Shopee: {shopee_link}\n")
print(f"🛍 Lazada: {lazada_link}\n")
print("🔥 โปรโมชั่นมาแรง! รีบสั่งซื้อตอนนี้ก่อนสินค้าหมด 🔥")
