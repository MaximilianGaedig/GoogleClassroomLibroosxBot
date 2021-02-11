import os
import platform
import time
import asyncio
import selenium
import yaml
from datetime import datetime
from win10toast import ToastNotifier
from libroosx import keychain_proxy_login, SynAClient
from libroosx.librocache import SQLiteCacheConnector, CacheBridge
from libroosx.utils import fetch_timetable
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    ElementNotInteractableException,
    ElementClickInterceptedException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium import webdriver
import chromedriver_autoinstaller

if platform.system() == 'windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

chromedriver_autoinstaller.install()
driver_options = Options()
driver_options.add_argument("start-minimized")
driver_options.add_argument("use-fake-ui-for-media-stream")
driver_options.add_experimental_option("useAutomationExtension", False)
driver_options.add_experimental_option("excludeSwitches", ["enable-automation"])
driver_options.add_argument("user-data-dir=./profile")
close_msg = "Unable to evaluate script: disconnected: not connected to DevTools\n"
toaster = ToastNotifier()


def log(event):
    event = str(event)
    log_message = datetime.now().strftime("[%H:%M:%S] ") + event
    print(log_message)
    with open("bot.log", "a", encoding="utf-8") as log_file:
        log_file.write(log_message + "\n")
    toaster.show_toast(datetime.now().strftime("[%H:%M:%S] "), event, duration=3)


def classroom_login(config):
    if not config["logged_in"]:
        driver = webdriver.Chrome(options=driver_options)
        driver.get(
            "https://accounts.google.com/o/oauth2/v2/auth/oauthchooseaccount?redirect_uri=https%3A%2F%2F"
            "developers.google.com%2Foauthplayground&prompt=select_account&response_type=code&"
            "client_id=407408718192"
            ".apps.googleusercontent.com&scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fclassroom.announcements"
            "&access_type=offline&flowName=GeneralOAuthFlow"
        )
        print(
            "Log in to your google account (This is a workaround for being unable to log into google accounts in "
            "selenium)"
        )
        oauth_running = True
        while oauth_running:
            time.sleep(1)
            try:
                cancel_oauth = driver.find_element_by_xpath(
                    '//*[@id="submit_deny_access"]/div/button/div[2]'
                ).click()
                oauth_running = False
                log("Logged in")
                config["logged_in"] = True
                with open("config.yml", "w", encoding="utf-8") as f:
                    yaml.dump(config, f, allow_unicode=True)
            except NoSuchElementException:
                pass
        driver.close()


def join_classroom(classroom):
    driver = webdriver.Chrome(options=driver_options)
    driver.get("https://classroom.google.com")
    try:
        element = WebDriverWait(driver, 30).until(
            expected_conditions.presence_of_element_located(
                (By.PARTIAL_LINK_TEXT, classroom)
            )
        )
        log(f"Class {classroom} found")
        element.click()
    except TimeoutException:
        log(f"Class {classroom} not found")
    try:
        print("trying")
        link = (
            WebDriverWait(driver, 10)
            .until(
                expected_conditions.presence_of_element_located(
                    (By.PARTIAL_LINK_TEXT, "https://meet.google.com/")
                )
            )
            .text
        )
        log(f"Link found: {link}")
        driver.get(link)
    except TimeoutException:
        log("Link not found")
    loading = True
    while loading:
        try:
            reload_button = WebDriverWait(driver, 5).until(
                expected_conditions.presence_of_element_located(
                    (
                        By.XPATH,
                        '//*[@id="yDmH0d"]/c-wiz/div/div[2]/div[3]/div[1]/button/div[2]',
                    )
                )
            )
            driver.get(link)
            log("Reloading")
            time.sleep(5)
        except selenium.common.exceptions.TimeoutException:
            log(f"Loaded {classroom}")
            loading = False
    starting = True
    camera_button = driver.find_element_by_css_selector(
        "div[data-tooltip='Turn off microphone (ctrl + d)']"
    ).click()

    mic_button = driver.find_element_by_css_selector(
        "div[data-tooltip='Turn off camera (ctrl + e)']"
    ).click()
    while starting:
        try:
            enter_meeting_button = driver.find_element_by_xpath(
                "/html/body/div[1]/c-wiz/div/div/div[8]/div[3]/div/div/div[2]/div/div[1]/div[2]/div/div[2]/div/div[1]/div[1]/span/span"
            ).click()
            starting = False
            log(f"Class {classroom} has started")

        except (
            NoSuchElementException,
            ElementNotInteractableException,
            ElementClickInterceptedException,
        ) as e:
            print(e)
            log(f"Waiting for class {classroom} to start...")
            time.sleep(2)
    return driver


def leave_class(driver):
    log("Class ended")
    driver.close()


# ---------------------------------------------------------------------------
#                           Classroom define end
# --------------------------------------------------------------------------
async def librus_login():
    config = yaml.safe_load(open("config.yml", encoding="utf-8"))
    user = await keychain_proxy_login(
        config["librus"]["email"], config["librus"]["password"]
    )
    return SynAClient(user, cache=CacheBridge(SQLiteCacheConnector(":memory:")))  # Nie twórz sesji

# --------------------------------------------------------------------------
#                                Define end
# --------------------------------------------------------------------------
async def main():
    try:
        os.rename("bot.log", "bot.old.log")
    except WindowsError:
        try:
            os.remove("bot.old.log")
            os.rename("bot.log", "bot.old.log")
        except FileNotFoundError:
            pass
    log("Started Bot")
    while True:
        # First time setup
        try:
            # If you want to log in again change logged_in to False in the config.yml
            config = yaml.safe_load(open("config.yml", encoding="utf-8"))
            client = await librus_login()

            if not config["logged_in"]:
                classroom_login(config)
            if config["classroom"] is None:
                subjects = {}
                a = client
                for i in a:
                    subjects[str(i)] = ""
                config["classroom"] = subjects
                for i in config:
                    print(i)
                with open("config.yml", "w", encoding="utf-8") as f:
                    documents = yaml.dump(config, f, allow_unicode=True)
                print("set the classroom names manually")
                exit()
            active_lesson_old = None
            lesson_running = False
            while True:
                tt = None
                i = 0
                while tt is None and i <= 1:
                    tt = await fetch_timetable(client)
                    i = +1
                today_datetime = datetime.now()
                today_date = today_datetime.date()
                try:
                    active_lesson = tuple(
                        filter(
                            lambda x: x.hour_end > today_datetime.time() > x.hour_start,
                            tt.auto.get(today_date.strftime("%Y-%m-%d")),
                        )
                    )
                except AttributeError:
                    pass
                    active_lesson = None
                if active_lesson != active_lesson_old:
                    if active_lesson != () and active_lesson is not None:
                        if not lesson_running:
                            if config["classroom"][active_lesson[0].subject.name] != "":
                                # This code runs if the lesson has changed
                                # TODO: Check if lesson is not cancelled
                                # Starting classroom
                                driver = join_classroom(config["classroom"][active_lesson[0].subject.name])
                                lesson_running = True
                                highest_member_count = 0
                if lesson_running:
                    try:
                        member_count = int(
                            WebDriverWait(driver, 5)
                            .until(
                                expected_conditions.presence_of_element_located(
                                    (
                                        By.XPATH,
                                        '//*[@id="ow3"]/div[1]/div/div[8]/div[3]/div[1]/div[3]/div/div[2]/div[1]/span/span/div/div/span[2]',
                                    )
                                )
                            )
                            .text
                        )
                        if member_count > highest_member_count:
                            highest_member_count = member_count
                        if highest_member_count - 5 > member_count:
                            leave_class(driver)
                            lesson_running = False
                        print(member_count)
                    except selenium.common.exceptions.TimeoutException:
                        pass
                    except AttributeError:
                        pass
                if active_lesson is not None:
                    active_lesson_old = active_lesson
                time.sleep(10)
        except selenium.common.exceptions.WebDriverException as e:
            print(e)
            log("Browser closed")

        await client.close()


asyncio.run(main())


