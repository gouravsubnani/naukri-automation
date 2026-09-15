"""
Cookie Exporter for Naukri.com
-------------------------------
Opens a visible Chrome window so you can log in manually (including OTP).
Once you're logged in and on the profile/homepage, press Enter in this
terminal and it saves all Naukri cookies to 'naukri_cookies.json'.

Run this once (or whenever cookies expire, roughly every 30 days):
    python export_cookies.py
"""

import json
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

NAUKRI_LOGIN_URL = "https://www.naukri.com/nlogin/login"
COOKIES_FILE = Path(__file__).parent / "naukri_cookies.json"


def main() -> None:
    print("=" * 60)
    print("  Naukri Cookie Exporter")
    print("=" * 60)
    print()
    print("A Chrome window will open. Please:")
    print("  1. Log in to Naukri (enter email, password, OTP, etc.)")
    print("  2. Wait until you see your dashboard or homepage")
    print("  3. Come back here and press ENTER")
    print()

    # Launch visible Chrome (NOT headless)
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Remove webdriver footprint
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"},
    )

    driver.get(NAUKRI_LOGIN_URL)

    input("\n>> Press ENTER here after you have logged in successfully... ")

    # Give a moment for any final redirects
    time.sleep(2)

    # Grab all cookies
    cookies = driver.get_cookies()
    driver.quit()

    if not cookies:
        print("\nNo cookies found. Make sure you logged in before pressing Enter.")
        return

    # Save to file
    with open(COOKIES_FILE, "w", encoding="utf-8") as f:
        json.dump(cookies, f, indent=2)

    print(f"\nSaved {len(cookies)} cookies to: {COOKIES_FILE}")
    print()

    # Also print the JSON string for GitHub secrets
    cookies_json_str = json.dumps(cookies)
    print("=" * 60)
    print("  FOR GITHUB ACTIONS: Copy the text below and paste it")
    print("  as the NAUKRI_COOKIES secret in your GitHub repo.")
    print("=" * 60)
    print()
    print(cookies_json_str)
    print()

    # Copy to clipboard if possible
    try:
        import subprocess
        process = subprocess.Popen(
            ["clip"], stdin=subprocess.PIPE, shell=True
        )
        process.communicate(cookies_json_str.encode("utf-8"))
        print("(Also copied to clipboard!)")
    except Exception:
        print("(Could not copy to clipboard — please copy manually from above.)")

    print()
    print("Done! You can now run the automation or set up GitHub Actions.")


if __name__ == "__main__":
    main()
