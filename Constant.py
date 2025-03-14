import os
from dotenv import load_dotenv

load_dotenv()  # Load .env variables


class Constant:

    # WebDriver
    WEBDRIVER_PATH: str = os.environ.get("WEBDRIVER_PATH", "/usr/local/bin/chromedriver")
    WEBDRIVER_TIMEOUT = 30
    WEBDRIVER_TIMEOUT_EXISTENCE = 10

    # Scrapper refresh time
    SCRAPPER_REFRESH_TIME = 5

    # Scrapper execution window time
    INITIAL_TIME = 5
    FINAL_TIME = 23
