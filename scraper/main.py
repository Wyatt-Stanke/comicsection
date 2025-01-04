from io import BytesIO
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from datetime import date
import os
import requests
from PIL import Image
from datetime import timedelta

# Set up the Chrome WebDriver
options = webdriver.ChromeOptions()
options.add_argument("--ignore-certificate-errors")
options.add_argument("--ignore-certificate-errors-spki-list")
options.add_argument("--ignore-ssl-errors")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-extensions")
options.add_argument("--dns-prefetch-disable")
options.add_argument("--disable-gpu")
options.add_argument("--disable-default-apps")
options.add_argument("--disable-features=Translate")
options.add_argument("--disable-features=PrivacySandboxSettings4")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)


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
