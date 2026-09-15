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
    StaleElementReferenceException,
)
from webdriver_manager.chrome import ChromeDriverManager

from headline_generator import generate_headline

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_FILE = Path(__file__).parent / "naukri_automation.log"
SCREENSHOT_DIR = Path(__file__).parent / "screenshots"
SCREENSHOT_DIR.mkdir(exist_ok=True)

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
PAGE_LOAD_TIMEOUT = 60
ELEMENT_WAIT = 20
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
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
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


def _save_screenshot(driver: webdriver.Chrome, name: str) -> None:
    """Save a screenshot for debugging purposes."""
    try:
        path = SCREENSHOT_DIR / f"{name}.png"
        driver.save_screenshot(str(path))
        logger.info("Screenshot saved: %s", path)
    except Exception as e:
        logger.warning("Could not save screenshot: %s", e)


def _save_page_source(driver: webdriver.Chrome, name: str) -> None:
    """Save page source HTML for debugging."""
    try:
        path = SCREENSHOT_DIR / f"{name}.html"
        with open(path, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        logger.info("Page source saved: %s", path)
    except Exception as e:
        logger.warning("Could not save page source: %s", e)


def _find_element_by_selectors(driver, selectors, wait_time=ELEMENT_WAIT, description="element"):
    """Try multiple selectors to find an element. Returns the first match or None."""
    for by, selector in selectors:
        try:
            element = WebDriverWait(driver, wait_time).until(
                EC.presence_of_element_located((by, selector))
            )
            logger.info("Found %s using selector: %s", description, selector)
            return element
        except (TimeoutException, NoSuchElementException):
            continue
    return None


def _find_clickable_by_selectors(driver, selectors, wait_time=ELEMENT_WAIT, description="element"):
    """Try multiple selectors to find a clickable element. Returns the first match or None."""
    for by, selector in selectors:
        try:
            element = WebDriverWait(driver, wait_time).until(
                EC.element_to_be_clickable((by, selector))
            )
            logger.info("Found clickable %s using selector: %s", description, selector)
            return element
        except (TimeoutException, NoSuchElementException):
            continue
    return None


# ---------------------------------------------------------------------------
# Core actions
# ---------------------------------------------------------------------------

def login(driver: webdriver.Chrome) -> bool:
    """Log in to Naukri.com. Returns True on success."""
    logger.info("Navigating to Naukri login page...")
    driver.get(NAUKRI_LOGIN_URL)
    time.sleep(5)

    _save_screenshot(driver, "01_login_page")
    _save_page_source(driver, "01_login_page")

    # --- Find email field using multiple selectors ---
    logger.info("Looking for email field...")
    email_selectors = [
        (By.CSS_SELECTOR, "input[type='text'][placeholder*='Email']"),
        (By.CSS_SELECTOR, "input[type='text'][placeholder*='email']"),
        (By.CSS_SELECTOR, "input[type='text'][placeholder*='Username']"),
        (By.CSS_SELECTOR, "input[placeholder*='Email']"),
        (By.CSS_SELECTOR, "input[placeholder*='email']"),
        (By.CSS_SELECTOR, "input[id*='usernameField']"),
        (By.CSS_SELECTOR, "input[name='username']"),
        (By.CSS_SELECTOR, "input[name='email']"),
        (By.XPATH, "//input[@type='text'][contains(@placeholder, 'mail')]"),
        (By.XPATH, "//input[@type='text'][contains(@placeholder, 'Mail')]"),
        (By.XPATH, "//form//input[@type='text']"),
    ]

    email_field = _find_element_by_selectors(driver, email_selectors, description="email field")
    if not email_field:
        logger.error("Could not find email input field.")
        _save_screenshot(driver, "01_email_not_found")
        _save_page_source(driver, "01_email_not_found")
        # Log all visible inputs for debugging
        inputs = driver.find_elements(By.TAG_NAME, "input")
        for i, inp in enumerate(inputs):
            logger.info(
                "  Input #%d: type=%s, name=%s, id=%s, placeholder=%s",
                i, inp.get_attribute("type"), inp.get_attribute("name"),
                inp.get_attribute("id"), inp.get_attribute("placeholder"),
            )
        return False

    logger.info("Entering email...")
    email_field.clear()
    email_field.send_keys(NAUKRI_EMAIL)
    time.sleep(1)

    # --- Find password field ---
    logger.info("Looking for password field...")
    password_selectors = [
        (By.CSS_SELECTOR, "input[type='password']"),
        (By.CSS_SELECTOR, "input[placeholder*='assword']"),
        (By.CSS_SELECTOR, "input[name='password']"),
        (By.XPATH, "//input[@type='password']"),
    ]

    password_field = _find_element_by_selectors(driver, password_selectors, description="password field")
    if not password_field:
        logger.error("Could not find password input field.")
        _save_screenshot(driver, "02_password_not_found")
        return False

    logger.info("Entering password...")
    password_field.clear()
    password_field.send_keys(NAUKRI_PASSWORD)
    time.sleep(1)

    _save_screenshot(driver, "02_credentials_entered")

    # --- Find and click login button ---
    logger.info("Looking for login button...")
    login_selectors = [
        (By.CSS_SELECTOR, "button[type='submit']"),
        (By.XPATH, "//button[contains(text(), 'Login')]"),
        (By.XPATH, "//button[contains(text(), 'login')]"),
        (By.XPATH, "//button[contains(text(), 'Sign in')]"),
        (By.CSS_SELECTOR, "button.loginButton"),
        (By.CSS_SELECTOR, "input[type='submit']"),
        (By.XPATH, "//form//button"),
    ]

    login_btn = _find_clickable_by_selectors(driver, login_selectors, description="login button")
    if not login_btn:
        logger.error("Could not find login button.")
        _save_screenshot(driver, "03_login_btn_not_found")
        return False

    logger.info("Clicking login button...")
    login_btn.click()

    # Wait for login to complete
    time.sleep(8)
    _save_screenshot(driver, "03_after_login_click")

    # Check if login was successful
    current_url = driver.current_url.lower()
    if "login" in current_url and "nlogin" in current_url:
        logger.warning("Login may have failed — still on login page.")
        logger.warning("URL: %s", driver.current_url)
        _save_screenshot(driver, "03_login_failed")
        _save_page_source(driver, "03_login_failed")
        return False

    logger.info("Login successful! URL: %s", driver.current_url)
    return True


def upload_resume(driver: webdriver.Chrome) -> bool:
    """Navigate to profile and upload/re-upload the resume. Returns True on success."""
    logger.info("Navigating to profile page for resume upload...")
    driver.get(NAUKRI_PROFILE_URL)
    time.sleep(8)

    _save_screenshot(driver, "04_profile_page")

    resume_path_abs = str(Path(RESUME_PATH).resolve())
    logger.info("Resume path: %s", resume_path_abs)

    try:
        # Look for any file input on the page (Naukri uses hidden file inputs)
        logger.info("Looking for resume upload input...")

        file_input = None

        # Try specific selectors first, then generic
        file_selectors = [
            "input[type='file'][id='attachCV']",
            "input[type='file'][name='file']",
            "input[type='file'][id*='resume']",
            "input[type='file'][id*='cv']",
            "input[type='file'][accept*='pdf']",
            "input[type='file']",
        ]

        for selector in file_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    file_input = elements[0]
                    logger.info("Found file input with selector: %s", selector)
                    break
            except NoSuchElementException:
                continue

        if not file_input:
            # Try clicking an update/upload button first to reveal the file input
            logger.info("No file input found. Trying to click upload button first...")
            upload_btn_selectors = [
                (By.XPATH, "//*[contains(text(), 'Update resume')]"),
                (By.XPATH, "//*[contains(text(), 'update resume')]"),
                (By.XPATH, "//*[contains(text(), 'Upload Resume')]"),
                (By.XPATH, "//*[contains(text(), 'Upload resume')]"),
                (By.CSS_SELECTOR, "[class*='upload']"),
                (By.CSS_SELECTOR, "[class*='UpdateResume']"),
            ]

            upload_btn = _find_clickable_by_selectors(
                driver, upload_btn_selectors, wait_time=SHORT_WAIT, description="upload button"
            )
            if upload_btn:
                try:
                    upload_btn.click()
                    time.sleep(3)
                    file_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
                    if file_inputs:
                        file_input = file_inputs[0]
                        logger.info("Found file input after clicking upload button.")
                except (ElementClickInterceptedException, StaleElementReferenceException) as e:
                    logger.warning("Click on upload button failed: %s", e)

        if not file_input:
            logger.error("Could not find any file upload input on the page.")
            _save_screenshot(driver, "04_no_file_input")
            _save_page_source(driver, "04_no_file_input")
            return False

        # Make the file input visible (sometimes it's hidden)
        driver.execute_script(
            "arguments[0].style.display = 'block'; "
            "arguments[0].style.visibility = 'visible'; "
            "arguments[0].style.height = '1px'; "
            "arguments[0].style.width = '1px'; "
            "arguments[0].style.opacity = '1';",
            file_input,
        )
        time.sleep(1)

        logger.info("Uploading resume: %s", resume_path_abs)
        file_input.send_keys(resume_path_abs)
        time.sleep(8)

        _save_screenshot(driver, "05_after_upload")
        logger.info("Resume uploaded successfully!")
        return True

    except Exception as e:
        logger.error("Resume upload failed: %s", e)
        _save_screenshot(driver, "05_upload_error")
        return False


def update_headline(driver: webdriver.Chrome) -> bool:
    """Update the profile headline with a fresh keyword-rich tagline. Returns True on success."""
    logger.info("Navigating to profile page for headline update...")
    driver.get(NAUKRI_PROFILE_URL)
    time.sleep(8)

    _save_screenshot(driver, "06_profile_for_headline")

    new_headline = generate_headline()
    logger.info("New headline: %s", new_headline)

    try:
        # Find and click the edit icon near "Resume Headline"
        logger.info("Looking for headline edit button...")

        edit_clicked = False

        # Try multiple approaches to find the edit button
        edit_selectors = [
            # Direct class-based selectors
            (By.XPATH, "//*[contains(@class, 'resumeHeadline')]//span[contains(@class, 'edit')]"),
            (By.CSS_SELECTOR, ".resumeHeadline .editIcon"),
            (By.CSS_SELECTOR, ".resumeHeadline .edit-icon"),
            (By.CSS_SELECTOR, ".resumeHeadline [class*='edit']"),
            (By.CSS_SELECTOR, "[class*='resumeHeadline'] [class*='edit']"),
            (By.CSS_SELECTOR, "[class*='resumeHeadline'] [class*='icon']"),
            (By.XPATH, "//*[contains(@class, 'resumeHeadline')]//span[contains(@class, 'icon')]"),
            (By.XPATH, "//*[contains(@id, 'resumeHeadline')]//span[contains(@class, 'icon')]"),
        ]

        for by, selector in edit_selectors:
            try:
                element = driver.find_element(by, selector)
                element.click()
                edit_clicked = True
                logger.info("Clicked edit button using selector: %s", selector)
                break
            except (NoSuchElementException, ElementClickInterceptedException, StaleElementReferenceException):
                continue

        # Fallback: find "Resume Headline" text and look for edit icon nearby
        if not edit_clicked:
            logger.info("Trying to find headline section by text...")
            headline_text_selectors = [
                "//span[contains(text(), 'Resume headline')]",
                "//span[contains(text(), 'Resume Headline')]",
                "//*[contains(text(), 'Resume headline')]",
                "//*[contains(text(), 'Resume Headline')]",
            ]
            for xpath in headline_text_selectors:
                try:
                    headline_el = driver.find_element(By.XPATH, xpath)
                    # Look for clickable sibling or parent's child
                    parent = headline_el.find_element(By.XPATH, "./..")
                    clickable = parent.find_elements(By.CSS_SELECTOR, "span, a, button, [role='button']")
                    for el in clickable:
                        cls = el.get_attribute("class") or ""
                        if "edit" in cls.lower() or "icon" in cls.lower() or "pencil" in cls.lower():
                            el.click()
                            edit_clicked = True
                            logger.info("Clicked edit icon found near headline text.")
                            break
                    if edit_clicked:
                        break
                    # If no edit icon in parent, try grandparent
                    grandparent = parent.find_element(By.XPATH, "./..")
                    clickable = grandparent.find_elements(By.CSS_SELECTOR, "span, a, button, [role='button']")
                    for el in clickable:
                        cls = el.get_attribute("class") or ""
                        if "edit" in cls.lower() or "icon" in cls.lower() or "pencil" in cls.lower():
                            el.click()
                            edit_clicked = True
                            logger.info("Clicked edit icon found near headline text (grandparent).")
                            break
                    if edit_clicked:
                        break
                except (NoSuchElementException, ElementClickInterceptedException, StaleElementReferenceException):
                    continue

        if not edit_clicked:
            logger.error("Could not find the headline edit button.")
            _save_screenshot(driver, "06_edit_btn_not_found")
            _save_page_source(driver, "06_edit_btn_not_found")
            return False

        time.sleep(3)
        _save_screenshot(driver, "07_headline_edit_open")

        # Find the headline textarea
        logger.info("Looking for headline textarea...")
        textarea_selectors = [
            (By.CSS_SELECTOR, "#resumeHeadlineTxt"),
            (By.CSS_SELECTOR, "textarea[name*='headline']"),
            (By.CSS_SELECTOR, ".resumeHeadline textarea"),
            (By.CSS_SELECTOR, "[class*='resumeHeadline'] textarea"),
            (By.CSS_SELECTOR, "textarea"),
        ]

        textarea = _find_element_by_selectors(driver, textarea_selectors, description="headline textarea")
        if not textarea:
            logger.error("Could not find headline textarea.")
            _save_screenshot(driver, "07_textarea_not_found")
            return False

        logger.info("Clearing old headline and typing new one...")
        textarea.click()
        time.sleep(0.5)

        # Clear the textarea thoroughly
        textarea.send_keys(Keys.CONTROL, "a")
        time.sleep(0.3)
        textarea.send_keys(Keys.BACKSPACE)
        time.sleep(0.3)
        textarea.clear()
        time.sleep(0.3)

        textarea.send_keys(new_headline)
        time.sleep(1)

        _save_screenshot(driver, "08_headline_typed")

        # Click Save button
        logger.info("Looking for save button...")
        save_selectors = [
            (By.XPATH, "//button[contains(text(), 'Save')]"),
            (By.XPATH, "//button[contains(text(), 'save')]"),
            (By.CSS_SELECTOR, "button.btn-primary"),
            (By.CSS_SELECTOR, "button[type='submit']"),
            (By.XPATH, "//button[contains(@class, 'save')]"),
        ]

        save_btn = _find_clickable_by_selectors(driver, save_selectors, description="save button")
        if not save_btn:
            logger.error("Could not find save button.")
            _save_screenshot(driver, "08_save_not_found")
            return False

        save_btn.click()
        time.sleep(5)

        _save_screenshot(driver, "09_headline_saved")
        logger.info("Headline updated successfully!")
        return True

    except Exception as e:
        logger.error("Headline update failed: %s", e)
        _save_screenshot(driver, "09_headline_error")
        return False


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

        if not login(driver):
            logger.error("Login failed. Aborting remaining steps.")
            return

        upload_resume(driver)
        update_headline(driver)

        logger.info("All tasks completed!")

    except Exception as e:
        logger.error("Automation failed with error: %s", e)
        if driver:
            _save_screenshot(driver, "99_fatal_error")
            _save_page_source(driver, "99_fatal_error")
    finally:
        if driver:
            driver.quit()
            logger.info("Browser closed.")

    logger.info("=" * 60)
    logger.info("Run finished.")
    logger.info("=" * 60)


if __name__ == "__main__":
    run()
