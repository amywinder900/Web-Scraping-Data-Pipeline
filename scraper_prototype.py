
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

    def accept_cookies(self) -> webdriver.Chrome:
        print("Accepting cookies")
        self.navigate_to(self.URL)
        time.sleep(2)
        accept_cookies_button = self.driver.find_element_by_xpath("//button[@id='banner-cookie-consent-allow-all']")
        accept_cookies_button.click()
    
    def retrieve_links_from_current_page(self):
        time.sleep(2)
        print("Retrieving links")
        products = self.driver.find_elements_by_xpath("//*[@class='g4m-grid-product-listing']/a")
        page_list_of_product_urls = [product.get_attribute("href") for product in products]
        return page_list_of_product_urls
    
    def retrieve_links(self):
        list_of_product_urls = []
        for i in range(2):
            url = "https://www.gear4music.com/podcasting/microphones?" + "page=" + str(i+1)
            print("Current page is", url )
            self.navigate_to(url)
            list_of_product_urls.append(self.retrieve_links_from_current_page())
        print(len(list_of_product_urls))
        print(list_of_product_urls)
        return list_of_product_urls
            

# %%
if __name__ == "__main__":
    gear4music = scraper("https://www.gear4music.com/podcasting/microphones?")
    gear4music.accept_cookies()
    gear4music.retrieve_links()

# %%


# %%
