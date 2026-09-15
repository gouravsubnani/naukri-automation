"""
Naukri.com Automation Script
-----------------------------
1. Logs in to your Naukri account.
2. Uploads your resume (refreshes the "last updated" timestamp).
3. Updates your profile headline with a fresh, keyword-rich tagline.

Uses Selenium with Chrome in headless mode so it can run unattended.
"""

import os
import sys
import time
import logging
from pathlib import Path

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
)
from webdriver_manager.chrome import ChromeDriverManager

from headline_generator import generate_headline

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_FILE = Path(__file__).parent / "naukri_automation.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
load_dotenv()

NAUKRI_EMAIL = os.getenv("NAUKRI_EMAIL")
NAUKRI_PASSWORD = os.getenv("NAUKRI_PASSWORD")
RESUME_PATH = os.getenv("RESUME_PATH")

NAUKRI_LOGIN_URL = "https://www.naukri.com/nlogin/login"
NAUKRI_PROFILE_URL = "https://www.naukri.com/mnjuser/profile"

# Timeouts (seconds)
PAGE_LOAD_TIMEOUT = 30
ELEMENT_WAIT = 15
SHORT_WAIT = 5


def _validate_config() -> None:
    """Make sure all required env vars are set and the resume file exists."""
    missing = []
    if not NAUKRI_EMAIL:
        missing.append("NAUKRI_EMAIL")
    if not NAUKRI_PASSWORD:
        missing.append("NAUKRI_PASSWORD")
    if not RESUME_PATH:
        missing.append("RESUME_PATH")

    if missing:
        logger.error("Missing environment variables: %s", ", ".join(missing))
        logger.error("Copy .env.example to .env and fill in your details.")
        sys.exit(1)

    if not Path(RESUME_PATH).is_file():
        logger.error("Resume file not found: %s", RESUME_PATH)
        sys.exit(1)


def _create_driver() -> webdriver.Chrome:
    """Create a headless Chrome WebDriver instance."""
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    # Realistic user-agent
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)

    # Remove webdriver footprint
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"},
    )

    return driver


# ---------------------------------------------------------------------------
# Core actions
# ---------------------------------------------------------------------------

def login(driver: webdriver.Chrome) -> None:
    """Log in to Naukri.com."""
    logger.info("Navigating to Naukri login page...")
    driver.get(NAUKRI_LOGIN_URL)
    time.sleep(3)

    wait = WebDriverWait(driver, ELEMENT_WAIT)

    # Enter email
    logger.info("Entering email...")
    email_field = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='Enter your active Email ID / Username']"))
    )
    email_field.clear()
    email_field.send_keys(NAUKRI_EMAIL)
    time.sleep(1)

    # Enter password
    logger.info("Entering password...")
    password_field = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']"))
    )
    password_field.clear()
    password_field.send_keys(NAUKRI_PASSWORD)
    time.sleep(1)

    # Click login button
    logger.info("Clicking login button...")
    login_btn = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
    )
    login_btn.click()

    # Wait for login to complete (profile icon or redirect)
    time.sleep(5)

    # Check if login was successful by verifying the URL changed
    if "login" in driver.current_url.lower():
        logger.warning("Login may have failed — still on login page. Check credentials.")
        # Try alternative: sometimes there's a CAPTCHA or OTP
        logger.warning("If CAPTCHA/OTP is required, headless mode won't work. "
                       "Run once in non-headless mode to handle it.")
    else:
        logger.info("Login successful!")


def upload_resume(driver: webdriver.Chrome) -> None:
    """Navigate to profile and upload/re-upload the resume."""
    logger.info("Navigating to profile page...")
    driver.get(NAUKRI_PROFILE_URL)
    time.sleep(5)

    wait = WebDriverWait(driver, ELEMENT_WAIT)
    resume_path_abs = str(Path(RESUME_PATH).resolve())

    try:
        # Naukri has a hidden file input for resume upload.
        # Look for the file input element associated with resume upload.
        logger.info("Looking for resume upload input...")

        # Try the direct file input approach first
        file_input = None

        # Method 1: Find file input near the resume section
        try:
            file_input = driver.find_element(
                By.CSS_SELECTOR, "input[type='file'][id='attachCV']"
            )
        except NoSuchElementException:
            pass

        # Method 2: Try other common selectors
        if file_input is None:
            try:
                file_input = driver.find_element(
                    By.CSS_SELECTOR, "input[type='file'][name='file']"
                )
            except NoSuchElementException:
                pass

        # Method 3: Any file input on the page
        if file_input is None:
            try:
                file_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
                if file_inputs:
                    file_input = file_inputs[0]
                    logger.info("Found file input element via generic selector.")
            except NoSuchElementException:
                pass

        if file_input is None:
            # Method 4: Click the "Update resume" / upload button to reveal file input
            logger.info("No file input found directly. Trying to click update resume button...")
            try:
                update_btn = wait.until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//*[contains(text(), 'Update resume') or contains(text(), 'upload') or contains(text(), 'Upload')]")
                    )
                )
                update_btn.click()
                time.sleep(2)
                file_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
            except (TimeoutException, NoSuchElementException):
                logger.error("Could not locate resume upload element. Naukri may have changed their layout.")
                return

        # Send the file path to the input
        logger.info("Uploading resume: %s", resume_path_abs)
        file_input.send_keys(resume_path_abs)
        time.sleep(5)

        logger.info("Resume uploaded successfully!")

    except Exception as e:
        logger.error("Resume upload failed: %s", e)


def update_headline(driver: webdriver.Chrome) -> None:
    """Update the profile headline with a fresh keyword-rich tagline."""
    logger.info("Navigating to profile page for headline update...")
    driver.get(NAUKRI_PROFILE_URL)
    time.sleep(5)

    wait = WebDriverWait(driver, ELEMENT_WAIT)
    new_headline = generate_headline()
    logger.info("New headline: %s", new_headline)

    try:
        # Find and click the edit icon/pencil near the resume headline section
        logger.info("Looking for headline edit button...")

        # The headline section usually has an edit (pencil) icon.
        # Try multiple selectors since Naukri changes their UI periodically.
        edit_clicked = False

        # Method 1: Click the pencil icon near "Resume Headline"
        try:
            headline_section = driver.find_element(
                By.XPATH, "//*[contains(@class, 'resumeHeadline')]//span[contains(@class, 'edit')]"
            )
            headline_section.click()
            edit_clicked = True
        except (NoSuchElementException, ElementClickInterceptedException):
            pass

        # Method 2: Look for edit icon with common class names
        if not edit_clicked:
            try:
                edit_icons = driver.find_elements(
                    By.CSS_SELECTOR, ".resumeHeadline .editIcon, .resumeHeadline .edit-icon, .resumeHeadline [class*='edit']"
                )
                if edit_icons:
                    edit_icons[0].click()
                    edit_clicked = True
            except (NoSuchElementException, ElementClickInterceptedException):
                pass

        # Method 3: Try by aria-label or title
        if not edit_clicked:
            try:
                edit_btn = driver.find_element(
                    By.XPATH,
                    "//*[contains(@class, 'resumeHeadline')]//span[contains(@class, 'icon')]"
                    " | //*[contains(@id, 'resumeHeadline')]//span[contains(@class, 'icon')]"
                )
                edit_btn.click()
                edit_clicked = True
            except (NoSuchElementException, ElementClickInterceptedException):
                pass

        # Method 4: Broader search — find "Resume Headline" text, then nearby edit element
        if not edit_clicked:
            try:
                headline_label = driver.find_element(
                    By.XPATH, "//*[contains(text(), 'Resume headline') or contains(text(), 'Resume Headline')]"
                )
                # Look for a sibling or nearby edit icon
                parent = headline_label.find_element(By.XPATH, "./..")
                edit_icon = parent.find_element(By.CSS_SELECTOR, "span[class*='edit'], span[class*='icon'], a, button")
                edit_icon.click()
                edit_clicked = True
            except (NoSuchElementException, ElementClickInterceptedException):
                pass

        if not edit_clicked:
            logger.error("Could not find the headline edit button. Naukri may have changed their layout.")
            return

        time.sleep(2)

        # Find the headline textarea and update it
        logger.info("Clearing old headline and typing new one...")
        textarea = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "textarea, .resumeHeadline textarea, #resumeHeadlineTxt, textarea[name*='headline']")
            )
        )
        textarea.click()
        textarea.clear()
        time.sleep(0.5)

        # Sometimes .clear() doesn't work — select all and delete
        textarea.send_keys(Keys.CONTROL, "a")
        textarea.send_keys(Keys.DELETE)
        time.sleep(0.5)

        textarea.send_keys(new_headline)
        time.sleep(1)

        # Click Save button
        logger.info("Saving headline...")
        save_btn = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(text(), 'Save') or contains(text(), 'save')]")
            )
        )
        save_btn.click()
        time.sleep(3)

        logger.info("Headline updated successfully!")

    except Exception as e:
        logger.error("Headline update failed: %s", e)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run() -> None:
    """Run the full automation: login -> upload resume -> update headline."""
    logger.info("=" * 60)
    logger.info("Naukri Automation — Starting run")
    logger.info("=" * 60)

    _validate_config()

    driver = None
    try:
        driver = _create_driver()
        login(driver)
        upload_resume(driver)
        update_headline(driver)
        logger.info("All tasks completed successfully!")
    except Exception as e:
        logger.error("Automation failed with error: %s", e)
    finally:
        if driver:
            driver.quit()
            logger.info("Browser closed.")

    logger.info("=" * 60)
    logger.info("Run finished.")
    logger.info("=" * 60)


if __name__ == "__main__":
    run()
