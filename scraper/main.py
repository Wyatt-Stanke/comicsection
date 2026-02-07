import os
from datetime import date, datetime, time, timedelta
from io import BytesIO
import traceback

import requests
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from utils import build_gocomics_url, get_image_path, get_placeholder_path, get_chrome_version



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

for option in options:
    chrome_options.add_argument(option)

# Gives a speedup by not waiting for the full page to load
chrome_options.page_load_strategy = "eager"

current_chrome_version = get_chrome_version()
url = f"https://clients2.google.com/service/update2/crx?response=redirect&prodversion={current_chrome_version}&acceptformat=crx2,crx3&x=id%3Dcjpalhdlnbpafiamejdnhcphjbkeiagm%26uc"

# Use a cached uBlock Origin CRX when available, and clean up old versions
dest_dir = "./.tmp"
os.makedirs(dest_dir, exist_ok=True)
dest_path = os.path.join(dest_dir, f"ublock_origin_{current_chrome_version}.crx")

if not os.path.exists(dest_path):
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    
    # Validate that we received a CRX file (should be binary content)
    if len(response.content) < 1000:  # CRX files are typically much larger
        raise ValueError("Downloaded CRX file appears to be too small or invalid")
    
    with open(dest_path, "wb") as f:
        f.write(response.content)

# Remove any old uBlock Origin CRX files for other Chrome versions
try:
    for filename in os.listdir(dest_dir):
        if not filename.startswith("ublock_origin_") or not filename.endswith(".crx"):
            continue
        full_path = os.path.join(dest_dir, filename)
        if full_path != dest_path and os.path.isfile(full_path):
            os.remove(full_path)
except OSError:
    # Best-effort cleanup; ignore any filesystem errors here
    pass
chrome_options.add_extension(dest_path)

driver = webdriver.Chrome(options=chrome_options)

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

# Allow overriding via environment variables for testing
_comics_env = os.getenv("SCRAPER_COMICS")
if _comics_env:
    followedComics = [c.strip() for c in _comics_env.split(",") if c.strip()]

DAYS_PAST = int(os.getenv("SCRAPER_DAYS", "7"))
BASE_DIR = os.getenv("SCRAPER_BASE_DIR", "..")


def scrape_job(comic_name, job_func, days_past, **kwargs):
    print(f"Scraping {comic_name} for the last {days_past} days")
    for i in range(days_past):
        comic_date = date.today() - timedelta(days=i)
        image_path = get_image_path(comic_name, comic_date, base_dir=BASE_DIR)
        place_holder_path = get_placeholder_path(comic_name, comic_date, base_dir=BASE_DIR)
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
    scrape_job(comic, gocomics, DAYS_PAST, comic=comic)
