from io import BytesIO
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
from datetime import date
import os
import requests
from PIL import Image
from datetime import timedelta

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


def getComicAtDate(comic, comicDate):
    if os.path.exists(
        os.path.join("..", "comics", comic, comicDate.strftime("%Y-%m-%d"), "comic.png")
    ):
        print(f"{comic} for {comicDate} already exists")
        return
    year = comicDate.year
    month = comicDate.month
    day = comicDate.day
    driver.get(f"https://www.gocomics.com/{comic}/{year}/{month}/{day}")
    try:
        alertElement = driver.find_element(
            By.CSS_SELECTOR, "div.amu-container-alert > div"
        )
        print(f"Comic {comic} for {comicDate} not published yet")
        return
    except:
        pass
    comicElement = driver.find_element(
        By.CSS_SELECTOR, "div.comic__container > div > a > picture > img"
    )
    comicUrl = comicElement.get_attribute("src")
    # Create the directory if it doesn't exist
    comic_dir = os.path.join("..", "comics", comic, comicDate.strftime("%Y-%m-%d"))
    os.makedirs(comic_dir, exist_ok=True)

    # Download the comic image
    response = requests.get(comicUrl)
    image = Image.open(BytesIO(response.content))
    image.save(os.path.join(comic_dir, "comic.png"))
    print(f"Downloaded {comic} for {comicDate}")


followedComics = ["bignate", "pearlsbeforeswine"]

for comic in followedComics:
    for i in range(8):
        comicDate = date.today() - timedelta(days=i)
        getComicAtDate(comic, comicDate)
