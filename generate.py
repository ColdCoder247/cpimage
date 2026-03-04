import os
import random
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
USED_FILE = os.path.join(BASE_DIR, "used_coins.txt")

os.makedirs(OUTPUT_DIR, exist_ok=True)

USD_TO_INR = 83


# -------------------------
# Utilities
# -------------------------

def format_number(num):

    if num >= 1_000_000_000:
        return f"{round(num/1_000_000_000,2)}B"

    if num >= 1_000_000:
        return f"{round(num/1_000_000,2)}M"

    if num >= 1_000:
        return f"{round(num/1_000,2)}K"

    return str(round(num,2))


def fetch_top_100():

    url = "https://api.coingecko.com/api/v3/coins/markets"

    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 100,
        "page": 1,
        "sparkline": "true",
        "price_change_percentage": "24h,7d"
    }

    return requests.get(url, params=params).json()


def fetch_trending():

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
    used = used[-30:]

    with open(USED_FILE, "w") as f:
        f.write("\n".join(used))


# -------------------------
# Render Image
# -------------------------

def render(template_name, output_name, replacements):

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

        page = browser.new_page(viewport={"width":1200,"height":900})

        page.goto(f"file://{temp_file}")

        page.wait_for_timeout(1500)

        page.screenshot(path=os.path.join(OUTPUT_DIR, output_name))

        browser.close()


# -------------------------
# Template Data Builder
# -------------------------

def build_replacements(coin):

    price = coin["current_price"]
    price_inr = price * USD_TO_INR

    change24 = coin.get("price_change_percentage_24h",0)
    change7d = coin.get("price_change_percentage_7d_in_currency",0)

    spark = coin.get("sparkline_in_7d",{}).get("price",[])
    spark_trim = spark[-60:]

    sparkline = ",".join([str(round(p,2)) for p in spark_trim])

    updated = datetime.utcnow().strftime("%d %b %Y %H:%M UTC")

    return {

        "{{coin_name}}": coin["name"],
        "{{symbol}}": coin["symbol"].upper(),
        "{{logo_url}}": coin["image"],

        "{{price_usd}}": f"{price:,.2f}",
        "{{price_inr}}": f"{int(price_inr):,}",

        "{{change}}": round(change24,2),
        "{{change7d}}": round(change7d,2),

        "{{rank}}": coin["market_cap_rank"],

        "{{market_cap}}": format_number(coin["market_cap"]),
        "{{volume}}": format_number(coin["total_volume"]),
        "{{supply}}": format_number(coin["circulating_supply"]),

        "{{sparkline_data}}": sparkline,

        "{{updated_time}}": updated
    }


# -------------------------
# MAIN
# -------------------------

data = fetch_top_100()
used = load_used()


# RANDOM COIN

available = [c for c in data if c["id"] not in used]

if not available:
    available = data

random_coin = random.choice(available)

save_used(random_coin["id"])

render(
    "square.html",
    "random_coin.png",
    build_replacements(random_coin)
)


# TOP GAINER

gainer = sorted(
    data,
    key=lambda x: x["price_change_percentage_24h"] or 0,
    reverse=True
)[0]

render(
    "square.html",
    "top_gainer.png",
    build_replacements(gainer)
)


# TOP LOSER

loser = sorted(
    data,
    key=lambda x: x["price_change_percentage_24h"] or 0
)[0]

render(
    "square.html",
    "top_loser.png",
    build_replacements(loser)
)


# TRENDING

trending_ids = fetch_trending()

trending = [c for c in data if c["id"] in trending_ids]

trend_coin = random.choice(trending) if trending else random.choice(data)

render(
    "square.html",
    "trending_coin.png",
    build_replacements(trend_coin)
)


# GAINER VS LOSER CARD

render(
    "gainer_loser.html",
    "gainer_vs_loser.png",
    {
        "{{gainer_name}}": gainer["name"],
        "{{gainer_price}}": gainer["current_price"],
        "{{gainer_change}}": round(gainer["price_change_percentage_24h"],2),
        "{{gainer_logo}}": gainer["image"],

        "{{loser_name}}": loser["name"],
        "{{loser_price}}": loser["current_price"],
        "{{loser_change}}": round(loser["price_change_percentage_24h"],2),
        "{{loser_logo}}": loser["image"]
    }
)


print("All images generated successfully")
