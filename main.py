import platform
import sys
import threading
import asyncio

from httpx import CloseError
from playsound import playsound
import selenium
from datetime import datetime, time
from libroosx import keychain_proxy_login, SynAClient
from libroosx.librocache import SQLiteCacheConnector, CacheBridge
from libroosx.utils import fetch_timetable
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    ElementNotInteractableException,
    ElementClickInterceptedException, StaleElementReferenceException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium import webdriver
import chromedriver_autoinstaller
import os
import yaml
import os


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


config = yaml.safe_load(open("config.yml", encoding='utf-8'))

if platform.system() == 'windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

chromedriver_autoinstaller.install(cwd=True)
driver_options = Options()
# driver_options.add_argument("start-minimized")
driver_options.add_experimental_option("useAutomationExtension", False)
driver_options.add_experimental_option("excludeSwitches", ["enable-automation"])
driver_options.add_argument("user-data-dir=./profile")
driver_options.add_argument("--disable-gpu")
close_msg = "Unable to evaluate script: disconnected: not connected to DevTools\n"


async def log(event):
    event = str(event)
    log_message = datetime.now().strftime("[%H:%M:%S] ") + event
    print(log_message)
    with open("bot.log", "a", encoding="utf-8") as log_file:
        log_file.write(log_message + "\n")


async def teams_login(config):
    if not config["logged_in"]:
        driver = webdriver.Chrome(options=driver_options)
        driver.get('https://teams.microsoft.com/')
        WebDriverWait(driver, 50).until(
            expected_conditions.presence_of_element_located(
                (
                    By.XPATH,
                    '//*[@id="download-desktop-page"]/div/a',
                )
            )
        ).click()
        print(
            "Log in to your Microsoft Teams account"
        )
        driver.close()
        await log("Logged in [Classroom]")


async def classroom_login(config):
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
            "Log in to your google account"
        )
        WebDriverWait(driver, 50).until(
            expected_conditions.presence_of_element_located(
                (
                    By.XPATH,
                    '//*[@id="submit_deny_access"]/div/button/div[2]',
                )
            )
        ).click()
        config["logged_in"] = True
        with open("config.yml", "w", encoding="utf-8") as f:
            yaml.dump(config, f, allow_unicode=True)
        driver.close()
        await log("Logged in [Classroom]")


async def join_meet(link, driver):
    # Waiting for Camera Button to appear and joining
    while True:
        try:
            if config["language"] == "pl":
                mic_button = WebDriverWait(driver, 5).until(
                    expected_conditions.presence_of_element_located(
                        (
                            By.CSS_SELECTOR,
                            'div[aria-label="Wyłącz mikrofon (Ctrl + D)"]',
                        )
                    )
                ).click()
                camera_button = WebDriverWait(driver, 5).until(
                    expected_conditions.presence_of_element_located(
                        (
                            By.CSS_SELECTOR,
                            'div[aria-label="Wyłącz kamerę (Ctrl + E)"]',
                        )
                    )
                ).click()
                # Joining
                join_btns = driver.find_elements_by_css_selector('[role="button"]')
                while True:
                    for btn in join_btns:
                        if btn.text == 'Dołącz':
                            btn.click()
                            break
                        elif btn.text == 'Chcę dołączyć':
                            btn.click()
                            break
                    else:
                        await asyncio.sleep(0.5)
                        continue
                    break
            elif config["language"] == "en":
                mic_button = WebDriverWait(driver, 5).until(
                    expected_conditions.presence_of_element_located(
                        (
                            By.CSS_SELECTOR,
                            'div[aria-label="Turn off microphone (ctrl + d)"]',
                        )
                    )
                ).click()
                camera_button = WebDriverWait(driver, 5).until(
                    expected_conditions.presence_of_element_located(
                        (
                            By.CSS_SELECTOR,
                            'div[aria-label="Turn off camera (ctrl + e)"]',
                        )
                    )
                ).click()
                # Joining
                join_btns = driver.find_elements_by_css_selector('div[role="button"]')
                while True:
                    for btn in join_btns:
                        if btn.text == 'Join now':
                            btn.click()
                            break
                        elif btn.text == 'Ask to join':
                            btn.click()
                            break
                    else:
                        await asyncio.sleep(0.5)
                        continue
                    break

            else:
                continue
            break
        except (
                NoSuchElementException,
                ElementNotInteractableException,
                ElementClickInterceptedException,
                StaleElementReferenceException,
                TimeoutException
        ):
            driver.get(link)
            try:
                error_message = WebDriverWait(driver, 5).until(
                    expected_conditions.presence_of_element_located(
                        (
                            By.XPATH,
                            '//*[@id="yDmH0d"]/c-wiz/div/div[2]/div[1]',
                        )
                    )
                ).text
                await log(error_message)
            except TimeoutException:
                pass
            await log("Reloading")
    return driver


async def join_classroom(classroom):
    if "teams:" in classroom:
        print("Teams")
        link = classroom.replace('teams:', '')
        driver = webdriver.Chrome(options=driver_options)
        return driver
        driver.get(link)
        while True:
            try:
                join_button = WebDriverWait(driver, 5).until(
                    expected_conditions.presence_of_element_located(
                        (
                            By.CSS_SELECTOR,
                            'button[track-summary="Join an ongoing meetup from the channel ongoing meeting object"]',
                        )
                    )
                ).click()
                mic_button = WebDriverWait(driver, 5).until(
                    expected_conditions.presence_of_element_located(
                        (
                            By.XPATH,
                            '//*[@id="preJoinAudioButton"]',
                        )
                    )
                )
            except TimeoutException:
                print(mic_button.get_attribute("title"))
                break
            return True
            # camera_button = WebDriverWait(driver, 5).until(
            #     expected_conditions.presence_of_element_located(
            #         (
            #             By.XPATH,
            #             '//*[@id="page-content-wrapper"]/div[1]/div/calling-pre-join-screen/div/div/div[2]/div[1]/div[2]/div/div/section/div[2]/toggle-button[1]',
            #         )
            #     )
            # ).click()
        # join_now_button = '//*[@id="page-content-wrapper"]/div[1]/div/calling-pre-join-screen/div/div/div[2]/div[1]/div[2]/div/div/section/div[1]/div/div/button'

    elif "link:" in classroom:
        print("Link")
        link = classroom.replace('link:', '')
        driver = webdriver.Chrome(options=driver_options)
        await join_meet(link, driver)
        return driver
    else:
        driver = webdriver.Chrome(options=driver_options)
        driver.get("https://classroom.google.com")
        while True:
            try:
                element = WebDriverWait(driver, 30).until(
                    expected_conditions.presence_of_element_located(
                        (By.PARTIAL_LINK_TEXT, classroom)
                    )
                )
                await log(f"Class {classroom} found")
                element.click()
                break
            except TimeoutException:
                await log(f"Class {classroom} not found")
        # Getting Link
        while True:
            try:
                link = (
                    WebDriverWait(driver, 10)
                    .until(
                        expected_conditions.presence_of_element_located(
                            (
                                By.PARTIAL_LINK_TEXT,
                                "https://meet.google.com/"
                            )
                        )
                    )
                ).text
                await log(f"Link found: {link}")
                break
            except TimeoutException:
                await log("Link not found")
        await join_meet(link, driver)
        return driver


async def leave_class(driver):
    await log("Class ended")
    driver.close()


async def librus_login():
    config = yaml.safe_load(open("config.yml", encoding="utf-8"))
    user = await keychain_proxy_login(
        config["librus"]["email"], config["librus"]["password"]
    )
    return SynAClient(user, cache=CacheBridge(SQLiteCacheConnector(":memory:")))


# --------------------------------------------------------------------------
#                                Functions end
# --------------------------------------------------------------------------

if __name__ == '__main__':
    async def main():
        # await bot.wait_until_ready()
        try:
            os.rename("bot.log", "bot.old.log")
        except WindowsError:
            try:
                os.remove("bot.old.log")
                os.rename("bot.log", "bot.old.log")
            except FileNotFoundError:
                pass
        await log("Started Bot")
        while True:
            # try:
            # First time setup
            # If you want to log in again change logged_in to False in the config.yml
            config = yaml.safe_load(open("config.yml", encoding="utf-8"))
            client = await librus_login()

            if not config["logged_in"]:
                await classroom_login(config)
            if config["classroom"] is None:
                subjects = {}
                a = client
                for i in a:
                    subjects[str(i)] = ""
                config["classroom"] = subjects
                for i in config:
                    print(i)
                with open("config.yml", "w", encoding="utf-8") as f:
                    yaml.dump(config, f, allow_unicode=True)
                print("set the classroom names manually")
                exit()
            active_lesson_old = None
            lesson_running = False
            while True:
                tt = None
                i = 0
                today_datetime = datetime.now()
                today_date = today_datetime.date()
                today_weekday = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][
                    today_date.weekday()]
                config = yaml.safe_load(open("config.yml", encoding="utf-8"))
                try:
                    tt_overrides = []
                    for override in config['overrides'][today_weekday]:
                        override_hour_start = datetime.strptime(str(override['hour_start']), '%H:%M').time()
                        override_hour_end = datetime.strptime(str(override['hour_end']), '%H:%M').time()
                        tt_overrides.append((override_hour_start, override_hour_end, override['lesson']))
                    active_lesson = tuple(
                        filter(
                            lambda x: x[1] > today_datetime.time() > x[0],
                            tt_overrides,
                        )
                    )[0][2]
                except (AttributeError, IndexError, TypeError):
                    pass
                    active_lesson = None
                if active_lesson is None or active_lesson == ():
                    while tt is None and i <= 1:
                        try:
                            tt = await fetch_timetable(client)
                            active_lesson = tuple(
                                filter(
                                    lambda x: x.hour_end > today_datetime.time() > x.hour_start,
                                    tt.auto.get(today_date.strftime('%Y-%m-%d')),
                                )
                            )[0].subject.name
                            i = +1
                        except (AttributeError, IndexError, CloseError):
                            pass
                            active_lesson = None
                if lesson_running:
                    try:
                        if driver.get_log('driver')[-1]['message'] == close_msg:
                            print('Browser window closed by user')
                            lesson_running = False
                    except (IndexError, TypeError):
                        pass
                    except UnboundLocalError:
                        print('Browser window closed by user')
                        lesson_running = False
                if lesson_running:
                    try:
                        member_count = int(
                            WebDriverWait(driver, 5).until(
                                expected_conditions.presence_of_element_located(
                                    (
                                        By.XPATH,
                                        '//*[@id="ow3"]/div[1]/div/div[9]/div[3]/div[1]/div[3]/div/div[2]/div[1]/span/span/div/div/span[2]',
                                    )
                                )
                            ).text
                        )
                        if member_count > highest_member_count:
                            highest_member_count = member_count
                        if highest_member_count * 0.75 > member_count:
                            await leave_class(driver)
                            lesson_running = False
                        print(
                            f"{member_count} people on the lesson, {highest_member_count} was the maximum, {highest_member_count * 0.75} at most are required to leave")
                    except (
                            selenium.common.exceptions.TimeoutException,
                            ValueError,
                            UnboundLocalError,
                            AttributeError
                    ):
                        pass
                if active_lesson != active_lesson_old and active_lesson != () and active_lesson is not None and not lesson_running:
                    await log(f"current:{active_lesson} old:{active_lesson_old}")
                    await log(f"{active_lesson} is the current lesson")
                    if config["classroom"][active_lesson] != "":
                        if active_lesson != 'cancelled':
                            # This code runs if the lesson has changed
                            # Starting classroom
                            lesson_running = True
                            threading.Thread(target=playsound, args=(resource_path('notification.mp3'),),
                                             daemon=True).start()
                            try:
                                driver = await join_classroom(config["classroom"][active_lesson])
                            except Exception as e:
                                await log(e)
                            highest_member_count = 0
                        else:
                            await log("Lesson cancelled")
                    else:
                        await log("It doesn't have a name/link in the config!")
                if active_lesson is not None:
                    active_lesson_old = active_lesson
                await asyncio.sleep(config["wait_time"])
        # except Exception as e:
        #     await log(e)


    asyncio.run(main())
