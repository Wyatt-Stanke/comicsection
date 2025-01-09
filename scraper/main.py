import os
from datetime import date, timedelta
from io import BytesIO

import requests
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

chrome_service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())

chrome_options = Options()
options = [
    "--headless=new",
    "--disable-gpu",
    "--window-size=1920,1200",
    "--ignore-certificate-errors",
    "--disable-extensions",
    "--no-sandbox",
    "--disable-dev-shm-usage",
]
for option in options:
    chrome_options.add_argument(option)

driver = webdriver.Chrome(service=chrome_service, options=chrome_options)


def gocomics(comic_date, comic=None):
    if comic is None:
        raise ValueError("Comic name is required")

    year = comic_date.year
    month = comic_date.month
    day = comic_date.day
    driver.get(f"https://www.gocomics.com/{comic}/{year}/{month}/{day}")
    try:
        _ = driver.find_element(By.CSS_SELECTOR, "div.amu-container-alert > div")
        print(f"Comic {comic} for {comic_date} not published yet")
        return None
    except:
        pass
    comic_element = driver.find_element(
        By.CSS_SELECTOR, "div.comic__container > div > a > picture > img"
    )
    comic_url = comic_element.get_attribute("src")

    # Download the comic image
    response = requests.get(comic_url)
    return Image.open(BytesIO(response.content))


# TODO: Allow getting previous
def candorville(comicDate):
    if comicDate < date.today():
        raise ValueError("Can't get previous comics")
    driver.get("https://www.candorville.com/candorville/")
    comic_element = driver.find_element(
        By.CSS_SELECTOR, "#spliced-comic > span.default-lang > picture > img"
    )
    comic_url = comic_element.get_attribute("src")
    response = requests.get(comic_url)
    return Image.open(BytesIO(response.content))


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
        image_path = os.path.join(
            "..", "comics", comic_name, comic_date.strftime("%Y-%m-%d"), "comic.png"
        )
        place_holder_path = os.path.join(
            "..", "comics", comic_name, comic_date.strftime("%Y-%m-%d"), ".placeholder"
        )
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        if os.path.exists(image_path):
            print(f"Comic {comic_name} for {comic_date} already exists")
            continue
        if os.path.exists(place_holder_path):
            print(f"Comic {comic_name} for {comic_date} already not found")
        image = job_func(comic_date, **kwargs)
        if image is not None:
            image.save(image_path)
            print(f"Comic {comic_name} for {comic_date} saved")
        else:
            print(f"Comic {comic_name} for {comic_date} not found")
            # Save a placeholder file if the comic is not found
            with open(place_holder_path, "w+", encoding="utf-8") as f:
                f.write("")


for comic in followedComics:
    scrape_job(comic, gocomics, 7, comic=comic)
scrape_job("candorville", candorville, 1)
