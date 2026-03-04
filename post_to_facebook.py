import os
import requests
import shutil

OUTPUT_DIR = "output"
POSTED_DIR = "posted"

PAGE_ID = os.getenv("FB_PAGE_ID")
ACCESS_TOKEN = os.getenv("FB_PAGE_TOKEN")

os.makedirs(POSTED_DIR, exist_ok=True)


def post_image(image_path):

    url = f"https://graph.facebook.com/{PAGE_ID}/photos"

    files = {
        "source": open(image_path, "rb")
    }

    data = {
        "access_token": ACCESS_TOKEN,
        "caption": "Latest Crypto Market Update 🚀"
    }

    response = requests.post(url, files=files, data=data)

    print(response.json())

    return response.status_code == 200


for file in os.listdir(OUTPUT_DIR):

    path = os.path.join(OUTPUT_DIR, file)

    if file.endswith(".png"):

        success = post_image(path)

        if success:

            shutil.move(
                path,
                os.path.join(POSTED_DIR, file)
            )

            print("Moved to posted:", file)
