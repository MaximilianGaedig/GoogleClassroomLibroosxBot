import os
import gtts
import time
import asyncio
import selenium
import yaml
from libroosx.utils import fetch_timetable
from libroosx import SynAClient
from libroosx.keychain import keychain_proxy_login
from libroosx.librocache import CacheBridge, SQLiteCacheConnector
from datetime import datetime
from libroosx.synergia.mappings import SynSubject
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions

driver_options = Options()
driver_options.add_argument("start-minimized")
driver_options.add_argument("use-fake-ui-for-media-stream")
driver_options.add_experimental_option('useAutomationExtension', False)
driver_options.add_experimental_option("excludeSwitches", ["enable-automation"])
driver_options.add_argument("user-data-dir=./profile")
close_msg = 'Unable to evaluate script: disconnected: not connected to DevTools\n'

try:
    os.rename('bot.log', 'bot.old.log')
except WindowsError:
    try:
        os.remove('bot.old.log')
        os.rename('bot.log', 'bot.old.log')
    except FileNotFoundError:
        pass


def log(event):
    log_message = datetime.now().strftime("[%H:%M:%S] ") + event
    print(log_message)
    gtts.gTTS(event).save('tts.mp3')
    os.remove('tts.mp3')
    with open('bot.log', 'a', encoding='utf-8') as log_file:
        log_file.write(log_message + "\n")


def leave_class(driver):
    log("Class ended")
    driver.close()


async def librus_login():
    config = yaml.safe_load(open("config.yml", encoding='utf-8'))
    user = await keychain_proxy_login(config['librus']['email'], config['librus']['password'])
    return SynAClient(user, cache=CacheBridge(SQLiteCacheConnector(':memory:')))


def classroom_login(driver):
    driver.get('https://accounts.google.com/o/oauth2/v2/auth/oauthchooseaccount?redirect_uri=https%3A%2F%2F'
               'developers.google.com%2Foauthplayground&prompt=select_account&response_type=code&client_id=407408718192'
               '.apps.googleusercontent.com&scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fclassroom.announcements'
               '&access_type=offline&flowName=GeneralOAuthFlow')
    print("Log in to your google account (This is a workaround for being unable to log into google accounts in "
          "selenium)")


async def librus_check_for_subjects(client):
    subjects = {}
    a = await client.fetch('/Subjects', syn_obj=SynSubject)
    for i in a:
        subjects[str(i)] = ''
    return subjects


def join_classroom(lesson):
    classroom = config['classroom'][lesson]
    if classroom != '':
        driver = webdriver.Chrome(options=driver_options)
        driver.get('https://classroom.google.com')
        time.sleep(5)
        try:
            element = WebDriverWait(driver, 10).until(
                expected_conditions.presence_of_element_located((By.PARTIAL_LINK_TEXT, classroom))
            )
            log(f"Class {classroom} found")
            element.click()
        except TimeoutException:
            log(f"Class {classroom} not found")
        try:
            link = WebDriverWait(driver, 10).until(
                expected_conditions.presence_of_element_located(
                    (By.XPATH, '//*[@id="yDmH0d"]/div[2]/div[2]/div[1]/div/div[2]/div[2]/div/span/a/div'))).text
            log(f"Link found: {link}")
            driver.get(link)
        except TimeoutException:
            log("Link not found")
        loading = True
        while loading:
            try:
                reload_button = WebDriverWait(driver, 1).until(
                    expected_conditions.presence_of_element_located(
                        (By.XPATH, '//*[@id="yDmH0d"]/c-wiz/div/div[2]/div[3]/div[1]/button/div[2]')))
                driver.refresh()
                log("Reloading")
            except selenium.common.exceptions.TimeoutException:
                log(f"Loaded {classroom}")
                loading = False
        starting = True
        camera_button = driver.find_element_by_xpath(
            '//*[@id="yDmH0d"]/c-wiz/div/div/div[8]/div[3]/div/div/div[2]/div/div[1]/div[1]/div[1]/div/div[4]/div[2]/div/div').click()

        mic_button = driver.find_element_by_xpath(
            '//*[@id="yDmH0d"]/c-wiz/div/div/div[8]/div[3]/div/div/div[2]/div/div[1]/div[1]/div[1]/div/div[4]/div[1]/div/div/div').click()
        while starting:
            try:
                enter_meeting_button = driver.find_element_by_xpath(
                    '//*[@id="yDmH0d"]/c-wiz/div/div/div[8]/div[3]/div/div/div[2]/div/div[1]/div[2]/div/div[2]/div/div['
                    '1]/div[1]/span/span').click()
                starting = False
                log(f"Class {classroom} has started")

            except NoSuchElementException:
                log(f"Waiting for class {classroom} to start...")


# If you want to log in again change logged_in to False in the config.yml
config = yaml.safe_load(open("config.yml", encoding='utf-8'))
client = asyncio.run(librus_login())
if not config['logged_in']:
    driver = webdriver.Chrome(options=driver_options)
    classroom_login(driver)
    oauth_running = True
    while oauth_running:
        time.sleep(1)
        try:
            cancel_oauth = driver.find_element_by_xpath(
                '//*[@id="submit_deny_access"]/div/button/div[2]').click()
            oauth_running = False
            log('Logged in')
            config['logged_in'] = True
            with open('config.yml', 'w', encoding='utf-8') as f:
                documents = yaml.dump(config, f, allow_unicode=True)
        except NoSuchElementException:
            pass
    driver.close()
if config['classroom'] is None:
    config['classroom'] = asyncio.run(librus_check_for_subjects(client))
    for i in config:
        print(i)
    with open('config.yml', 'w', encoding='utf-8') as f:
        documents = yaml.dump(config, f, allow_unicode=True)
    print("set the classroom names manually")
    exit()
active_lesson_old = None
while True:
    print('running')
    try:
        tt = asyncio.run(fetch_timetable(client))
    except RuntimeError:
        pass
    today_datetime = datetime.now()
    today_date = today_datetime.date()
    active_lesson = tuple(
        filter(lambda x: x.hour_end >today_datetime.time() > x.hour_start,
               tt.auto.get(today_date.strftime('%Y-%m-%d'))))
    print(active_lesson)
    if active_lesson != active_lesson_old:
        if active_lesson != ():
            print(active_lesson[0].subject.name)
            # Starting classroom
            join_classroom(active_lesson[0].subject.name)
    active_lesson_old = active_lesson
    time.sleep(20)
