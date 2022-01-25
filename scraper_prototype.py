
#%%
from selenium import webdriver
import time
from selenium.webdriver.common.keys import Keys


class scraper():
    def __init__(self, URL):
        self.URL = URL
        self.driver = webdriver.Chrome()

    def navigate_to(self,URL) -> webdriver.Chrome:
        self.driver.get(URL)
        time.sleep(1)

    def load_and_bypass(self) -> webdriver.Chrome:
        email="johnsmith934812@gmail.com"
        password="as8U6!s"
        self.navigate_to(self.URL)
        accept_cookies_button = self.driver.find_element_by_xpath("//*[@data-control-name='ga-cookie.consent.accept.v3']")
        accept_cookies_button.click()
        time.sleep(2)
        email_input = self.driver.find_element_by_xpath("//*[@name='session_key']")
        password_input = self.driver.find_element_by_xpath("//*[@name='session_password']")
        email_input.send_keys(email)
        password_input.send_keys(password)
        password_input.send_keys(Keys.RETURN)
        time.sleep(2)
        # may be needed to bypass phone number pop up, wait and see
        # skip_button =self.driver.find_element_by_xpath("//*[class='secondary-action']")
        # skip_button.click()

    def search_item(self):
        search_url="https://www.linkedin.com/search/results/content/?keywords=edinburgh%20fringe%20festival&sortBy=%22date_posted%22"
        self.driver.get(search_url)

    def scroll(self):
        scroll_pause_time = 2
        i = 1 
        #currently scrolls five times
        while i < 5:
            time.sleep(scroll_pause_time)
            content_container = self.driver.find_elements_by_xpath("//div[@class='search-results-container']/div/div/div")
            index_last_element = len(content_container) - 1
            final_element = content_container[index_last_element]
            self.driver.execute_script("arguments[0].scrollIntoView()",final_element)
            i+=1
  
# %%
if __name__ == "__main__":
    linkedin = scraper("https://www.linkedin.com")
    linkedin.load_and_bypass()
    linkedin.search_item()
    linkedin.scroll()

# %%
