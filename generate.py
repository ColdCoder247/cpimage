import os
import requests
from playwright.sync_api import sync_playwright
from datetime import datetime

# ==========================================
# CONFIG
# ==========================================

COINS = ["bitcoin", "ethereum"]  # Add more coins here

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ==========================================
# HELPER: Format Large Numbers
# ==========================================

def format_number(num):
    if num >= 1_000_000_000:
        return f"{round(num/1_000_000_000,2)}B"
    elif num >= 1_000_000:
        return f"{round(num/1_000_000,2)}M"
    elif num >= 1_000:
        return f"{round(num/1_000,2)}K"
    else:
        return str(num)

# ==========================================
# FETCH MARKET DATA
# ==========================================

def get_data(coin):

    url = f"https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "ids": coin,
        "price_change_percentage": "24h"
    }

    response = requests.get(url, params=params)
    data = response.json()[0]

    return {
        "name": data["name"],
        "usd": data["current_price"],
        "inr": data["current_price"] * 83,  # approx conversion (fast + safe)
        "change": round(data["price_change_percentage_24h"], 2),
        "rank": data["market_cap_rank"],
        "market_cap": format_number(data["market_cap"]),
        "volume": format_number(data["total_volume"])
    }

# ==========================================
# RENDER IMAGE
# ==========================================

def render_image(template_name, output_name, width, height, replacements):

    template_path = os.path.join(TEMPLATE_DIR, template_name)

    if not os.path.exists(template_path):
        raise FileNotFoundError(f"{template_name} not found inside templates folder.")

    with open(template_path, "r", encoding="utf-8") as file:
        html = file.read()

    for key, value in replacements.items():
        html = html.replace(key, str(value))

    temp_file = os.path.join(BASE_DIR, "temp.html")
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(html)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height})
        page.goto(f"file://{temp_file}")
        page.wait_for_timeout(1000)
        page.screenshot(path=os.path.join(OUTPUT_DIR, output_name))
        browser.close()

# ==========================================
# MAIN EXECUTION
# ==========================================

for coin in COINS:

    print(f"Generating image for {coin}...")

    data = get_data(coin)

    updated_time = datetime.utcnow().strftime("%d %b %Y %H:%M UTC")
    color = "#00ff88" if data["change"] >= 0 else "#ff4d4d"

    replacements = {
        "{{coin_name}}": data["name"],
        "{{price_usd}}": data["usd"],
        "{{price_inr}}": int(data["inr"]),
        "{{change}}": data["change"],
        "{{rank}}": data["rank"],
        "{{market_cap}}": data["market_cap"],
        "{{volume}}": data["volume"],
        "{{color}}": color,
        "{{updated_time}}": updated_time
    }

    render_image(
        "square.html",
        f"{coin}_square.png",
        1080,
        1080,
        replacements
    )

print("✅ Professional crypto images generated successfully.")
