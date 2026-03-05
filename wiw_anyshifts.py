import os
import time
import logging
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    StaleElementReferenceException,
    WebDriverException
)

# =============== CONFIG ===============
LOGIN_URL = "https://login.wheniwork.com/"
MY_SCHEDULE_URL = "https://appx.wheniwork.com/myschedule"

load_dotenv()
EMAIL = os.getenv("WIW_EMAIL")
PASSWORD = os.getenv("WIW_PASS")

if not EMAIL or not PASSWORD:
    raise RuntimeError("Missing WIW_EMAIL or WIW_PASS in .env file.")

BRAVE_PATH = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
CHROMEDRIVER_PATH = r"D:\WebDrivers\chromedriver.exe"

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s - %(message)s")

claimed_shifts = set()

def find_first(driver, locators, timeout=10):
    end = time.time() + timeout
    while time.time() < end:
        for by, sel in locators:
            try:
                el = driver.find_element(by, sel)
                if el:
                    return el
            except Exception:
                continue
        time.sleep(0.3)
    return None

def login_successful(driver):
    try:
        if "/myschedule" in driver.current_url:
            return True
        if driver.find_elements(By.CSS_SELECTOR, 'a.nav-item-link[href="/myschedule"]'):
            return True
        if driver.find_elements(By.CSS_SELECTOR, "img.menu-avatar"):
            return True
        if driver.find_elements(By.CSS_SELECTOR, "div.container.my-schedule"):
            return True
    except Exception:
        return False
    return False

def setup_browser():
    options = Options()
    options.binary_location = BRAVE_PATH
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-dev-shm-usage")
    options.add_experimental_option("detach", False)

    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(60)
    logging.info("Browser started")
    return driver

def login(driver, timeout=40):
    logging.info("Navigating to login page...")
    driver.get(LOGIN_URL)

    email_locators = [(By.ID, "email"), (By.ID, "login-email"), (By.NAME, "email"), (By.CSS_SELECTOR, "input[type='email']")]
    pass_locators = [(By.ID, "password"), (By.ID, "login-password"), (By.NAME, "password"), (By.CSS_SELECTOR, "input[type='password']")]

    email_field = find_first(driver, email_locators, timeout=20)
    if not email_field:
        driver.save_screenshot("login_missing_email.png")
        raise RuntimeError("Email input not found.")

    password_field = find_first(driver, pass_locators, timeout=5)
    if not password_field:
        driver.save_screenshot("login_missing_password.png")
        raise RuntimeError("Password input not found.")

    email_field.clear()
    email_field.send_keys(EMAIL)
    password_field.clear()
    password_field.send_keys(PASSWORD)

    submit_locators = [(By.CSS_SELECTOR, "button[type='submit']"),
                       (By.XPATH, "//button[contains(., 'Log in') or contains(., 'Sign in') or contains(., 'Login')]")]
    submit_btn = find_first(driver, submit_locators, timeout=3)
    if submit_btn:
        try:
            driver.execute_script("arguments[0].click();", submit_btn)
        except Exception:
            submit_btn.click()
    else:
        password_field.send_keys(Keys.RETURN)

    try:
        WebDriverWait(driver, timeout).until(lambda d: login_successful(d))
        logging.info("Login successful.")
    except TimeoutException:
        driver.save_screenshot("login_failed.png")
        raise RuntimeError("Login did not complete within timeout. Screenshot saved as login_failed.png")

def normalize_text(s):
    return s.replace("\xa0", " ").strip()

def claim_all_available_shifts(driver):
    # assume we are already on MY_SCHEDULE_URL
    if "/myschedule" not in driver.current_url:
        driver.get(MY_SCHEDULE_URL)
        time.sleep(3)

    shift_cards = driver.find_elements(By.CSS_SELECTOR, "div.shift-card")
    if not shift_cards:
        logging.info("No open shift cards found.")
        return False

    logging.info(f"Found {len(shift_cards)} shift cards. Attempting to claim all.")
    found_any = False

    for card in shift_cards:
        try:
            try:
                time_el = card.find_element(By.TAG_NAME, "h3")
                shift_time = normalize_text(time_el.text)
            except (NoSuchElementException, StaleElementReferenceException):
                shift_time = "(unknown time)"

            if shift_time in claimed_shifts:
                logging.debug(f"Already claimed earlier: {shift_time}")
                continue

            logging.info(f"Attempting to claim shift: {shift_time}")
            try:
                driver.execute_script("arguments[0].scrollIntoView({behavior:'auto', block:'center'});", card)
            except Exception:
                pass
            time.sleep(0.3)

            # Find "Take Shift" button
            try:
                take_btn = card.find_element(By.XPATH, ".//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'take shift')]")
            except Exception:
                btns = card.find_elements(By.TAG_NAME, "button")
                take_btn = None
                for b in btns:
                    try:
                        if "take shift" in b.text.lower():
                            take_btn = b
                            break
                    except Exception:
                        continue

            if not take_btn:
                logging.debug(f"No Take Shift button for {shift_time}")
                continue

            # Click the take button
            try:
                driver.execute_script("arguments[0].click();", take_btn)
            except Exception:
                try:
                    take_btn.click()
                except Exception as e:
                    logging.warning(f"Could not click take button: {e}")
                    continue

            # Confirm
            confirmed = False
            for _ in range(10):
                try:
                    confirm_btns = driver.find_elements(By.XPATH, "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'take openshift')]")
                    if confirm_btns:
                        driver.execute_script("arguments[0].click();", confirm_btns[0])
                        confirmed = True
                        break
                except Exception:
                    pass
                time.sleep(0.4)

            claimed_shifts.add(shift_time)
            if confirmed:
                found_any = True
                logging.info(f"✅ Claimed shift: {shift_time}")
            else:
                logging.warning(f"⚠️ Confirmation not found for {shift_time}")

            time.sleep(1.5)

        except StaleElementReferenceException:
            continue
        except Exception as e:
            logging.warning(f"Error processing shift card: {e}")
            continue

    return found_any

def auto_loop(driver, refresh_interval=3, run_forever=True, runtime_minutes=None):
    start_ts = time.time()
    try:
        while True:
            if runtime_minutes and (time.time() - start_ts) > (runtime_minutes * 60):
                logging.info("Configured runtime reached; stopping loop.")
                break

            try:
                found = claim_all_available_shifts(driver)
                if found:
                    logging.info("Claimed shifts this pass. Waiting 10 seconds before next check.")
                    time.sleep(10)
                else:
                    logging.info(f"No available shifts found. Refreshing in {refresh_interval} seconds.")
                    time.sleep(refresh_interval)
                    driver.refresh()
                    time.sleep(3)
            except Exception as e:
                logging.error(f"Error in main loop: {e}")
                time.sleep(refresh_interval)
                try:
                    driver.refresh()
                except Exception:
                    pass

            if not run_forever and runtime_minutes is None:
                break
    except KeyboardInterrupt:
        logging.info("Interrupted by user.")
    finally:
        logging.info("Exiting loop.")

def main():
    driver = None
    try:
        driver = setup_browser()
        login(driver)
        driver.get(MY_SCHEDULE_URL)
        time.sleep(2)
        auto_loop(driver, refresh_interval=3, run_forever=True)
    except Exception as e:
        logging.error(f"Fatal error: {e}")
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
            # force close brave if necessary
            os.system("taskkill /IM brave.exe /F >nul 2>&1")

if __name__ == "__main__":
    main()
