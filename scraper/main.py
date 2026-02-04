import os
from datetime import date, datetime, time, timedelta
from io import BytesIO
import traceback

import requests
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from utils import build_gocomics_url, get_image_path, get_placeholder_path

chrome_options = Options()
options = [
    "--disable-gpu",
    "--window-size=1920,1200",
    "--ignore-certificate-errors",
    "--disable-extensions",
    "--no-sandbox",
    "--disable-dev-shm-usage",
]

if not os.getenv("DEBUG"):
    options.insert(0, "--headless=new")

if os.path.exists("./extras/ublock_origin.crx"):
    print("Using cached adblocker")
    chrome_options.add_extension("./extras/ublock_origin.crx")

for option in options:
    chrome_options.add_argument(option)

# Gives a speedup by not waiting for the full page to load
chrome_options.page_load_strategy = "eager"

driver = webdriver.Chrome(options=chrome_options)

current_chrome_version = driver.capabilities["browserVersion"]
os.makedirs("extras", exist_ok=True)
with open("extras/chrome_version.txt", "w+") as f:
    read_chrome_version = f.read()
    read_chrome_version = read_chrome_version.strip() if read_chrome_version else None
    if read_chrome_version != current_chrome_version:
        f.write(current_chrome_version)
        url = f"https://clients2.google.com/service/update2/crx?response=redirect&prodversion={current_chrome_version}&acceptformat=crx2,crx3&x=id%3Dcjpalhdlnbpafiamejdnhcphjbkeiagm%26uc"
        print(f"Chrome version updated, redownloading adblocker from {url}")
        response = requests.get(url)
        with open("extras/ublock_origin.crx", "wb") as f:
            f.write(response.content)


def gocomics(comic_date, comic=None):
    if comic is None:
        raise ValueError("Comic name is required")

    year = comic_date.year
    month = comic_date.month
    day = comic_date.day
    driver.get(build_gocomics_url(comic, comic_date))
    try:
        # TODO: Match text to see if the comic is not published yet
        # TODO: I can't do this anymore with this goddamn site
        _ = driver.find_element(
            By.CSS_SELECTOR,
            "div.amu-container-alert > div.gc-alert--warning",
        )
        print(f"Comic {comic} for {comic_date} not published yet")
        return None, datetime(year, month, day)
    except:
        pass
    comic_element = driver.find_elements(
        By.CSS_SELECTOR,
        "div > button > img",
    )[0]
    comic_url = comic_element.get_attribute("src")

    # Download the comic image
    response = requests.get(comic_url)
    return Image.open(BytesIO(response.content)), datetime(year, month, day)


followedComics = [
    "bignate",
    "pearlsbeforeswine",
    "luann",
    "brewsterrockit",
    "forbetterorforworse",
    "calvinandhobbes",
    "garfield",
    "pickles",
    "foxtrot",
    "doonesbury",
    "crabgrass",
    "daddyshome",
]


def scrape_job(comic_name, job_func, days_past, **kwargs):
    print(f"Scraping {comic_name} for the last {days_past} days")
    for i in range(days_past):
        comic_date = date.today() - timedelta(days=i)
        image_path = get_image_path(comic_name, comic_date)
        place_holder_path = get_placeholder_path(comic_name, comic_date)
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        if os.path.exists(image_path):
            print(f"Comic {comic_name} for {comic_date} already exists")
            continue
        if os.path.exists(place_holder_path):
            print(f"Comic {comic_name} for {comic_date} already not found")
            continue
        try:
            image, actual_date = job_func(comic_date, **kwargs)
            print(comic_date, actual_date)
            if datetime.combine(comic_date, time()) < actual_date:
                print(f"Comic {comic_name} for {comic_date} not published yet")
                continue
            if image is not None:
                image.save(image_path)
                print(f"Comic {comic_name} for {comic_date} saved")
            else:
                print(f"Comic {comic_name} for {comic_date} not found")
                if comic_date < date.today() - timedelta(days=3):
                    # Save a placeholder file if the comic is not found
                    with open(place_holder_path, "w+", encoding="utf-8") as f:
                        f.write("")
        except Exception as e:
            print(f"Failed to scrape {comic_name} for {comic_date}: {e}")

            traceback.print_exc()


for comic in followedComics:
    scrape_job(comic, gocomics, 7, comic=comic)
