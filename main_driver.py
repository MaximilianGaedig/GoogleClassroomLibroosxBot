from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from config_man import default_config

options = Options()
for a in default_config.chrome_args:
    options.add_argument(a)

for e in default_config.chrome_exp:
    options.add_experimental_option(**e)

driver = webdriver.Chrome(options=options)
