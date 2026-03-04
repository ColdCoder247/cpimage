import os
import requests
from playwright.sync_api import sync_playwright
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
USED_FILE = os.path.join(BASE_DIR, "used_coins.txt")

os.makedirs(OUTPUT_DIR, exist_ok=True)

USD_TO_INR = 83

# --------------------------------
# Utility
# --------------------------------

def format_number(num):

    if num >= 1_000_000_000:
        return f"{round(num/1_000_000_000,2)}B"

    if num >= 1_000_000:
        return f"{round(num/1_000_000,2)}M"

    if num >= 1_000:
        return f"{round(num/1_000,2)}K"

    return str(round(num,2))


def fetch_data():

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
# Fetch coin
# --------------------------------

data = fetch_data()

coin = data[0]

price = coin["current_price"]

price_inr = price * USD_TO_INR

change24 = coin["price_change_percentage_24h"] or 0
change7d = coin["price_change_percentage_7d_in_currency"] or 0

updated = datetime.utcnow().strftime("%d %b %Y %H:%M UTC")

sparkline = ",".join([str(p) for p in coin["sparkline_in_7d"]["price"]])

replacements = {

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

"{{updated_time}}": updated,

"{{color}}": "#00ff9c" if change24 >= 0 else "#ff4d4d"

}

render("square.html", f"{coin['id']}.png", 1080, 1080, replacements)

print("Image generated successfully")
