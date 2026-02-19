import requests
from playwright.sync_api import sync_playwright
import os

COINS = ["bitcoin", "ethereum"]

def get_data(coin):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd,inr&include_24hr_change=true"
    data = requests.get(url).json()[coin]
    return (
        data["usd"],
        data["inr"],
        round(data["usd_24h_change"], 2)
    )

def render_image(template_path, output_path, width, height, replacements):
    with open(template_path, "r") as file:
        html = file.read()

    for key, value in replacements.items():
        html = html.replace(key, str(value))

    temp_file = "temp.html"
    with open(temp_file, "w") as f:
        f.write(html)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height})
        page.goto(f"file://{os.path.abspath(temp_file)}")
        page.screenshot(path=output_path)
        browser.close()

for coin in COINS:

    usd, inr, change = get_data(coin)
    color = "#00ff88" if change >= 0 else "#ff4d4d"

    replacements = {
        "{{coin_name}}": coin.upper(),
        "{{price_usd}}": usd,
        "{{price_inr}}": inr,
        "{{change}}": change,
        "{{color}}": color
    }

    # Square 1080x1080
    render_image(
        "templates/square.html",
        f"{coin}_square.png",
        1080, 1080,
        replacements
    )

    # Story 1080x1920
    render_image(
        "templates/story.html",
        f"{coin}_story.png",
        1080, 1920,
        replacements
    )

    # YouTube 1920x1080
    render_image(
        "templates/youtube.html",
        f"{coin}_youtube.png",
        1920, 1080,
        replacements
    )

print("✅ All formats generated successfully.")
