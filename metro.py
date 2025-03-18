import os
import time
import requests
import schedule as schedule
from loguru import logger
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from datetime import datetime, time as dt_time
from zoneinfo import ZoneInfo
import webdriver_functions as wdfn
from selenium import webdriver
from Constant import Constant
from dotenv import load_dotenv

load_dotenv()  # Load .env variables


# logger.add("scrapper_metrobus_{time}.log", rotation="1 day", level="INFO")

HEADLESS = True
SCHEDULED = True

TESTING_URL: str = "https://incidentesmovilidad.cdmx.gob.mx/public/bandejaEstadoServicio.xhtml?idMedioTransporte=stc"

locator_table_container = "//tbody[contains(.,'EstadoServicio')]"
locator_table_rows = "//table/tbody/tr"
locator_next_page_button = "//a[@aria-label='Página siguiente']"

# Global variable to store previous scrape results
previous_results = None


def initialize_driver():
    # Setup webdriver as a service
    service = Service(Constant.WEBDRIVER_PATH)
    chrome_options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def initialize_headless_driver():
    # Setup webdriver as a service (headless)
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Enable headless mode
    chrome_options.add_argument("--no-sandbox")  # Bypass OS security model, Chromium only
    chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
    service = Service(Constant.WEBDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def perform_research():
    """
    Opens the Metro website, waits for the table to load,
    scrapes the desired data for metro lines, logs the values, and returns a dictionary of results.
    """

    if HEADLESS:
        driver = initialize_headless_driver()
    else:
        driver = initialize_driver()

    try:
        driver.get(TESTING_URL)

        wdfn.wait_for_element(driver, locator_table_container)

        # # Dictionary to hold Metro data
        all_metro_data = wdfn.get_all_pages_metro_values(
            driver,
            locator_table_rows,
            locator_next_page_button
        )

        for line_id, info in all_metro_data.items():
            logger.info(f"Line: {line_id} - {info}")

    except Exception as e:
        logger.exception("Error during research: %s", e)
        raise

    finally:
        driver.quit()

    return all_metro_data


def send_notification(line_number, line_data):
    """
    Sends a notification for a specific Metrobus line to its respective topic.

    The notification includes:
      - Metrobus Line number
      - Estado
      - Información adicional
      - Estaciones afectadas

    The topic URL follows the format:
      http://url/metrobus_linea_N
    where N is the metrobus line number (1 to 7).

    :param line_number: The metrobus line number (1 to 7)
    :param line_data: Dictionary with keys 'estado', 'info_adicional', and 'estaciones_afectadas'
    """
    ntfy_ip = os.environ.get("NTFY_IP")
    ntfy_port = os.environ.get("NTFY_PORT")
    logger.debug(f"Notify IP: {ntfy_ip}")
    logger.debug(f"Notify PORT: {ntfy_port}")

    try:
        topic = f"metro_linea_{line_number}"
        ntfy_url = f"http://{ntfy_ip}:{ntfy_port}/{topic}"
        logger.debug(f"Notify URL: {ntfy_url}")
        headers = {'Title': f'Metro Linea {line_number}'}
        message = (
            f"Estado: {line_data.get('estado', 'N/A')}\n"
            f"Información adicional: {line_data.get('info_adicional', 'N/A')}\n"
            f"Estaciones afectadas: {line_data.get('estaciones_afectadas', 'N/A')}"
        )
        response = requests.post(ntfy_url, data=message.encode('utf-8'), headers=headers)
        response.raise_for_status()  # Raises an exception for HTTP error responses
        logger.info(f"Notification sent successfully for line {line_number}")
    except Exception as e:
        logger.exception(f"Failed to send notification for line {line_number}: {e}")


def job():
    """
    Function that combines checking the website and sending a message
    Checks if the current Mexico City time is between 5 AM and 11 PM.
    If so, performs the scraping and compares the new data with previous data.
    For each metro line:
      - On the first run, if the data does not match the happy path (i.e.,
        'estado' is not 'Servicio Regular', or 'info_adicional' is not empty, or
        'estaciones_afectadas' is not 'Ninguna'), a notification is sent.
      - On subsequent runs, if any field has changed, a notification is sent
        to the corresponding topic (e.g., 'metro_linea_1').
    """
    try:
        # Set Mexico City timezone
        mexico_tz = ZoneInfo("America/Mexico_City")
        current_time_mexico = datetime.now(mexico_tz).time()

        # Only run if current time is between 5:00 and 23:00
        if not (dt_time(Constant.INITIAL_TIME, 0) <= current_time_mexico <= dt_time(Constant.FINAL_TIME, 0)):
            logger.info("Current time is outside the scheduled window. Skipping this run.")
            return
        else:
            logger.info("Current time is in Mexico. We are good to continue.")

        logger.info("Starting scraping job...")
        new_results = perform_research()
        global previous_results

        if previous_results is None:
            # First run: send notification if the data is not the happy path.
            for line_id, curr in new_results.items():
                estado = curr.get('estado', '')
                info_adicional = curr.get('informacion_adicional', '')
                estaciones_afectadas = curr.get('estaciones_afectadas', '')

                # Check if not in the “happy path”
                if (estado != "Servicio Regular"
                        or info_adicional.strip() != ""
                        or estaciones_afectadas != "Ninguna"):
                    try:
                        send_notification(line_id, curr)
                    except Exception as e:
                        logger.exception(f"Error sending initial notification for line {line_id}: {e}")
                else:
                    logger.info(f"Initial happy path for line {line_id}. No notification sent.")

            previous_results = new_results
            logger.info("Initial scrape completed.")
        else:
            # Subsequent runs: compare each line's values to previous values.
            for line_id, curr in new_results.items():
                prev = previous_results.get(line_id, {})
                if (prev.get('estado') != curr.get('estado') or
                        prev.get('estaciones_afectadas') != curr.get('estaciones_afectadas') or
                        prev.get('informacion_adicional') != curr.get('informacion_adicional')):
                    try:
                        send_notification(line_id, curr)
                    except Exception as e:
                        logger.exception(f"Error sending notification for line {line_id}: {e}")
                else:
                    logger.info(f"No changes detected for line {line_id}.")
            previous_results = new_results

    except Exception as e:
        logger.exception("Error in job: %s", e)


def main() -> None:

    if SCHEDULED:
        # Schedule the job every X time
        schedule.every(Constant.SCRAPPER_REFRESH_TIME).minutes.do(job)

        # Run the scheduled job
        while True:
            schedule.run_pending()
            time.sleep(1)

    else:
        # Run standalone without scheduler
        job()


if __name__ == '__main__':
    main()
