import os
import requests
from playwright.sync_api import sync_playwright
from datetime import datetime

# ==========================================
# CONFIG
# ==========================================

COINS = ["bitcoin", "ethereum"]  # Add more if needed

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")

OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ==========================================
# FETCH DATA
# ==========================================

def get_data(coin):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd,inr&include_24hr_change=true"
    response = requests.get(url)
    data = response.json()[coin]

    usd = data["usd"]
    inr = data["inr"]
    change = round(data["usd_24h_change"], 2)

    return usd, inr, change


# ==========================================
# RENDER FUNCTION
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
        page.wait_for_timeout(1000)  # ensure full render
        page.screenshot(path=os.path.join(OUTPUT_DIR, output_name))
        browser.close()


# ==========================================
# MAIN
# ==========================================

for coin in COINS:

    print(f"Generating images for {coin}...")

    usd, inr, change = get_data(coin)
    color = "#00ff88" if change >= 0 else "#ff4d4d"
    updated_time = datetime.utcnow().strftime("%d %b %Y %H:%M UTC")

    replacements = {
        "{{coin_name}}": coin.upper(),
        "{{price_usd}}": usd,
        "{{price_inr}}": inr,
        "{{change}}": change,
        "{{color}}": color,
        "{{updated_time}}": updated_time
    }

    # 1080x1080
    render_image("square.html", f"{coin}_square.png", 1080, 1080, replacements)

    # 1080x1920
    render_image("story.html", f"{coin}_story.png", 1080, 1920, replacements)

    # 1920x1080
    render_image("youtube.html", f"{coin}_youtube.png", 1920, 1080, replacements)

print("✅ All images generated successfully.")
