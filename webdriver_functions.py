import re
import time

from loguru import logger
from selenium.common import StaleElementReferenceException, TimeoutException, ElementNotVisibleException, \
    InvalidElementStateException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from Constant import Constant


# def wait_for_element(_driver, _element):
#     timeout = Constant.WEBDRIVER_TIMEOUT
#     ignored_exceptions = (StaleElementReferenceException,)
#     try:
#         element_present = ec.presence_of_element_located((By.XPATH, _element))
#         WebDriverWait(_driver, timeout, ignored_exceptions=ignored_exceptions).until(element_present)
#         element_visible = ec.presence_of_element_located((By.XPATH, _element))
#         WebDriverWait(_driver, timeout, ignored_exceptions=ignored_exceptions).until(element_visible)
#         element_clickable = ec.presence_of_element_located((By.XPATH, _element))
#         WebDriverWait(_driver, timeout, ignored_exceptions=ignored_exceptions).until(element_clickable)
#         logger.debug(f"Element found: {_element}")
#     except TimeoutException:
#         logger.debug(f"Timeout awaiting for element to load: {_element}")


def wait_for_element(_driver, _element):
    timeout = Constant.WEBDRIVER_TIMEOUT
    ignored_exceptions = (StaleElementReferenceException,)

    def _wait_for_condition(condition):
        return WebDriverWait(_driver, timeout, ignored_exceptions=ignored_exceptions).until(condition)

    try:
        # Wait for the element to be present in the DOM
        _wait_for_condition(ec.presence_of_element_located((By.XPATH, _element)))

        # Since StaleElementReferenceException might still occur, retry finding the element
        for attempt in range(3):  # Retry up to 3 times
            try:
                # Now, ensure it's visible (implies presence)
                element_visible = _wait_for_condition(ec.visibility_of_element_located((By.XPATH, _element)))
                # Ensure the element is clickable as well
                _wait_for_condition(ec.element_to_be_clickable((By.XPATH, _element)))
                logger.debug(f"Element found and interactable: {_element}")
                return element_visible  # Return the visible (and interactable) element
            except StaleElementReferenceException:
                logger.warning(f"StaleElementReferenceException caught, retrying... Attempt {attempt + 1}")
                if attempt == 2:  # If it's the last attempt, raise the exception
                    raise
    except TimeoutException:
        logger.error(f"Timeout awaiting for element: {_element}")


def write_on_element(_driver, _element, _text):
    wait_for_element(_driver, _element)
    _driver.find_element(By.XPATH, _element).clear()
    _driver.find_element(By.XPATH, _element).send_keys(_text)


def click(_driver, _element):
    wait_for_element(_driver, _element)
    _driver.find_element(By.XPATH, _element).click()


def get_value(_driver, _element) -> str:
    wait_for_element(_driver, _element)
    return _driver.find_element(By.XPATH, _element).get_attribute('value')


def get_text(_driver, _element) -> str:
    wait_for_element(_driver, _element)
    return _driver.find_element(By.XPATH, _element).text


def does_element_exist(_driver, _element):
    timeout = Constant.WEBDRIVER_TIMEOUT_EXISTENCE
    ignored_exceptions = (StaleElementReferenceException, ElementNotVisibleException, InvalidElementStateException,
                          NoSuchElementException)
    try:
        element_present = ec.presence_of_element_located((By.XPATH, _element))
        WebDriverWait(_driver, timeout, ignored_exceptions=ignored_exceptions).until(element_present)
        element_visible = ec.presence_of_element_located((By.XPATH, _element))
        WebDriverWait(_driver, timeout, ignored_exceptions=ignored_exceptions).until(element_visible)
        element_clickable = ec.presence_of_element_located((By.XPATH, _element))
        WebDriverWait(_driver, timeout, ignored_exceptions=ignored_exceptions).until(element_clickable)
        logger.debug(f"Element does exist: {_element}")
        return True
    except TimeoutException:
        logger.debug(f"Element does not exist: {_element}")
        return False


def get_elements(_driver, _element):
    wait_for_element(_driver, _element)
    return _driver.find_elements(By.XPATH, _element)


def get_element(_driver, _route, _element):
    wait_for_element(_driver, _element)
    if _route == "XPATH":
        return _driver.find_element(By.XPATH, _element)
    elif _route == "TAG":
        return _driver.find_element(By.TAG_NAME, _element)
    else:
        return None


def switch_to_iframe(_driver, iframe_id):
    timeout = Constant.WEBDRIVER_TIMEOUT_EXISTENCE
    try:
        iframe = WebDriverWait(_driver, timeout).until(ec.presence_of_element_located((By.ID, iframe_id)))
        _driver.switch_to.frame(iframe)
        logger.debug("Switched to iframe:", iframe_id)
    except Exception as e:
        logger.debug(f"Error: {e}")


def get_metro_values(_driver, _table_locator):
    # Initialize dictionary to hold line data
    lines_data = {}

    # Locate all table rows; adjust the selector to match your actual table
    rows = _driver.find_elements(By.XPATH, _table_locator)

    for row in rows:
        # Find the image in this row (adjust if the <img> is nested differently)
        img = row.find_element(By.TAG_NAME, "img")
        src = img.get_attribute("src")

        # Extract the line identifier from the src, e.g. "/jakarta.fac/img/iconos/stc12.svg" -> "12"
        # A simple regex capturing what's after 'stc' and before '.svg'
        match = re.search(r'stc([^.]+)\.svg', src)
        if not match:
            # If for some reason it doesn't match, skip or handle differently
            continue

        line_id = match.group(1)  # e.g. "1", "12", "A", "B", etc.
        logger.debug(f"Linea de metro obtenida: {line_id}")

        # Now, collect the other columns in the row
        # Adjust indexing based on how many columns there actually are
        cols = row.find_elements(By.TAG_NAME, "td")

        # Columns are: [Line, Estado, Estaciones Afectadas, Info Adicional]
        if len(cols) == 4:
            estado = cols[1].text
            estaciones_afectadas = cols[2].text
            info_adicional = cols[3].text
        else:
            logger.exception("Seems that table changed its layout. Review the site!!!")
            raise Exception("Table layout mismatch")

        # Store in dictionary keyed by the line_id
        lines_data[line_id] = {
            "estado": estado,
            "estaciones_afectadas": estaciones_afectadas,
            "informacion_adicional": info_adicional
        }

    return lines_data


def get_all_pages_metro_values(_driver, _locator_table_rows, _locator_next_page_button):
    """
    Repeatedly clicks the 'Página siguiente' link until it becomes disabled,
    collecting data on each page.

    :param _driver: Selenium WebDriver
    :param _locator_table_rows: XPATH or CSS locator string for table rows
    :param _locator_next_page_button: XPATH or CSS locator string for the 'Página siguiente' link
    :return: A dictionary of line data from all pages
    """
    # Dictionary to accumulate data across pages
    all_data = {}

    while True:
        # Scrape current page
        page_data = get_metro_values(_driver, _locator_table_rows)

        # Merge current page’s data into all_data
        for k, v in page_data.items():
            all_data[k] = v

        # Find the next-page button
        next_button = _driver.find_element(By.XPATH, _locator_next_page_button)

        # Check if it's disabled
        classes = next_button.get_attribute("class")
        if "ui-state-disabled" in classes:
            logger.debug("Next page button is disabled. Reached last page.")
            break
        else:
            logger.debug("Clicking next page button.")
            next_button.click()
            # Wait a bit or use explicit wait to let the table refresh
            time.sleep(2)

    return all_data
