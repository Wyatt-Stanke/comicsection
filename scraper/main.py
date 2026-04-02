import asyncio
import os
from datetime import date, datetime, time, timedelta
from io import BytesIO
import traceback

import requests
from PIL import Image
import zendriver as zd
from pathlib import Path

from utils import (
    build_gocomics_url,
    get_image_path,
    get_placeholder_path,
)


async def gocomics(driver: zd.Browser, comic_date, comic=None):
    if comic is None:
        raise ValueError("Comic name is required")

    year = comic_date.year
    month = comic_date.month
    day = comic_date.day
    page = await driver.get(build_gocomics_url(comic, comic_date))
    await page.wait(1)

    try:
        # TODO: Match text to see if the comic is not published yet
        # TODO: I can't do this anymore with this goddamn site
        _ = await page.select(
            "div.amu-container-alert > div.gc-alert--warning", timeout=3
        )
        print(f"Comic {comic} for {comic_date} not published yet")
        return None, datetime(year, month, day)
    except:
        pass

    try:
        comic_element = (await page.select_all("div > button > img", timeout=20))[0]
    except:
        debug_path = Path(f"./debug/{comic}_{comic_date}.debug.png")
        debug_path.parent.mkdir(parents=True, exist_ok=True)
        await page.save_screenshot(debug_path.expanduser().resolve())

        raise

    comic_url = comic_element.attrs["src"]

    # Download the comic image
    response = requests.get(comic_url)
    return Image.open(BytesIO(response.content)), datetime(year, month, day)


async def scrape_job(driver, comic_name, job_func, days_past, BASE_DIR, **kwargs):
    print(f"Scraping {comic_name} for the last {days_past} days")
    for i in range(days_past):
        comic_date = date.today() - timedelta(days=i)
        image_path = get_image_path(comic_name, comic_date, base_dir=BASE_DIR)
        place_holder_path = get_placeholder_path(
            comic_name, comic_date, base_dir=BASE_DIR
        )
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        if os.path.exists(image_path):
            print(f"Comic {comic_name} for {comic_date} already exists")
            continue
        if os.path.exists(place_holder_path):
            print(f"Comic {comic_name} for {comic_date} already not found")
            continue
        try:
            image, actual_date = await job_func(driver, comic_date, **kwargs)
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


async def __main__():
    import sys

    config = zd.Config(
        browser_args=[
            "--disable-gpu",
            "--window-size=1920,1200",
            "--ignore-certificate-errors",
            "--disable-dev-shm-usage",
        ],
        headless=not os.getenv("HEADED"),
        browser_executable_path=os.getenv("CHROME_PATH", None) or None,
        sandbox=False,
        browser_connection_timeout=2,
        browser_connection_max_tries=10,
    )

    try:
        driver = await asyncio.wait_for(zd.start(config=config), timeout=60)
    except asyncio.TimeoutError:
        print("ERROR: Browser start timed out after 60 seconds")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Browser start failed: {e}")
        sys.exit(1)

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

    for comic in followedComics:
        await scrape_job(driver, comic, gocomics, DAYS_PAST, BASE_DIR, comic=comic)


if __name__ == "__main__":
    asyncio.run(__main__())
