import os
from time import sleep

if os.path.exists('profile'):
    raise Exception('usuń folder profile')

from config_man import ConfingMan
from main_driver import driver

if __name__ == '__main__':
    config = ConfingMan()
    email, passwd = config.google_credentials
    driver.get('https://meet.google.com')
    login_a = driver.find_elements_by_css_selector('a[event-action="sign in"]')[0]
    login_a.click()

    if not config.conf_dict.get('google').get('perform_auto_login'):
        exit()

    email_box = driver.find_elements_by_css_selector('[autocomplete="username"')[0]
    email_box.send_keys(email)
    driver.find_elements_by_css_selector('#identifierNext')[0].click()
    sleep(2)  # TODO: add await for element
    pass_box = driver.find_elements_by_css_selector('[type="password"]')[0]
    pass_box.send_keys(passwd)
    driver.find_elements_by_css_selector('#passwordNext')[0].click()
    sleep(2)  # TODO: add await for element
    driver.close()
