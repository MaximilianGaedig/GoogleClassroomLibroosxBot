from time import sleep
from typing import Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

from main_driver import driver as default_driver


class MeetController:
    def __init__(self, driver=default_driver):
        self.driver = driver

    def new_tab(self, url: Optional[str] = None):
        self.driver.execute_script("window.open('');")
        self.driver.switch_to.window(self.driver.window_handles[-1])
        if url is not None:
            self.driver.get(url)

    def join_meet(self, meet_url: str):
        self.driver.get(meet_url)
        WebDriverWait(self.driver, 4).until(expected_conditions.presence_of_element_located(
            (By.XPATH, "//*[contains(text(), 'Dołącz')]")
        ))

        sleep(1)
        join_btns = self.driver.find_elements_by_css_selector('[role="button"]')

        sleep(1)
        for btn in join_btns:
            if btn.text == 'Dołącz':
                sleep(0.5)
                btn.click()
                sleep(0.5)
                self.driver.find_elements_by_css_selector('[aria-label="Wyłącz mikrofon (Ctrl + D)"]')[0].click()
                self.driver.find_elements_by_css_selector('[aria-label="Wyłącz kamerę (Ctrl + E)"]')[0].click()
                break
