import os
import requests
import random
from playwright.sync_api import sync_playwright
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
USED_FILE = os.path.join(BASE_DIR, "used_coins.txt")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# --------------------------------
# Utility Functions
# --------------------------------

def format_number(num):
    if num >= 1_000_000_000:
        return f"{round(num/1_000_000_000,2)}B"
    elif num >= 1_000_000:
        return f"{round(num/1_000_000,2)}M"
    elif num >= 1_000:
        return f"{round(num/1_000,2)}K"
    return str(num)

def fetch_top_100():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 100,
        "page": 1,
        "price_change_percentage": "24h"
    }
    return requests.get(url, params=params).json()

def get_trending():
    url = "https://api.coingecko.com/api/v3/search/trending"
    data = requests.get(url).json()
    return [coin["item"]["id"] for coin in data["coins"]]

def load_used():
    if not os.path.exists(USED_FILE):
        return []
    with open(USED_FILE, "r") as f:
        return f.read().splitlines()

def save_used(coin_id):
    used = load_used()
    used.append(coin_id)
    used = used[-20:]
    with open(USED_FILE, "w") as f:
        f.write("\n".join(used))

# --------------------------------
# Detect Post Type Automatically
# --------------------------------

def get_post_type():
    now = datetime.utcnow()
    weekday = now.weekday()
    hour = now.hour

    if weekday == 6 and hour < 10:
        return "weekly"

    if hour < 8:
        return "top"
    elif hour < 12:
        return "gainer"
    elif hour < 16:
        return "trending"
    else:
        return "gainer_vs_loser"

# --------------------------------
# Render Image
# --------------------------------

def render(template_name, output_name, width, height, replacements):

    template_path = os.path.join(TEMPLATE_DIR, template_name)

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

# --------------------------------
# Main Logic
# --------------------------------

data = fetch_top_100()
post_type = get_post_type()
used = load_used()

print(f"Running post type: {post_type}")

# WEEKLY TOP 10
if post_type == "weekly":

    top10 = data[:10]

    replacements = {}
    for i, coin in enumerate(top10):
        replacements[f"{{{{coin{i}_name}}}}"] = coin["name"]
        replacements[f"{{{{coin{i}_price}}}}"] = coin["current_price"]
        replacements[f"{{{{coin{i}_logo}}}}"] = coin["image"]

    render("top10.html", "weekly_top10.png", 1080, 1080, replacements)
    exit()

# NIGHT: GAINER VS LOSER
if post_type == "gainer_vs_loser":

    sorted_data = sorted(data, key=lambda x: x["price_change_percentage_24h"] or 0)
    loser = sorted_data[0]
    gainer = sorted_data[-1]

    replacements = {
        "{{gainer_name}}": gainer["name"],
        "{{gainer_price}}": gainer["current_price"],
        "{{gainer_change}}": round(gainer["price_change_percentage_24h"],2),
        "{{gainer_logo}}": gainer["image"],
        "{{loser_name}}": loser["name"],
        "{{loser_price}}": loser["current_price"],
        "{{loser_change}}": round(loser["price_change_percentage_24h"],2),
        "{{loser_logo}}": loser["image"],
    }

    render("gainer_loser.html", "gainer_vs_loser.png", 1080, 1080, replacements)
    exit()

# SINGLE COIN POSTS

if post_type == "top":
    coin = data[0]

elif post_type == "gainer":
    coin = sorted(data, key=lambda x: x["price_change_percentage_24h"] or 0, reverse=True)[0]

elif post_type == "trending":
    trending_ids = get_trending()
    trending = [c for c in data if c["id"] in trending_ids]
    coin = trending[0] if trending else data[1]

# Prevent duplicate
if coin["id"] in used:
    for c in data:
        if c["id"] not in used:
            coin = c
            break

save_used(coin["id"])

replacements = {
    "{{coin_name}}": coin["name"],
    "{{price_usd}}": coin["current_price"],
    "{{change}}": round(coin["price_change_percentage_24h"],2),
    "{{rank}}": coin["market_cap_rank"],
    "{{logo_url}}": coin["image"],
}

render("square.html", f"{coin['id']}.png", 1080, 1080, replacements)

print("Done.")
