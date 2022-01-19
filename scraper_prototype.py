
#%%
from selenium import webdriver
import time

class scraper():
    def __init__(self, URL):
        self.URL = URL
        self.driver = webdriver.Chrome()

    def navigate_to(self,URL) -> webdriver.Chrome:
        self.driver.get(URL)
        time.sleep(1)

    def load_and_bypass(self) -> webdriver.Chrome:
        self.navigate_to(self.URL)
        accept_cookies_button = self.driver.find_element_by_xpath("//*[@data-control-name='ga-cookie.consent.accept.v3']")
        accept_cookies_button.click()
        time.sleep(30)

# %%
linkedin = scraper("https://www.linkedin.com/searchd")
linkedin.load_and_bypass()
# %%
