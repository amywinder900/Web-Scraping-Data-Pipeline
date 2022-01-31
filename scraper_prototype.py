
# %%
from email.mime import image
from selenium import webdriver
import time
import uuid
# %%


class scraper():
    def __init__(self, URL):
        self.URL = URL
        self.driver = webdriver.Chrome()

    def navigate_to(self, URL) -> webdriver.Chrome:
        self.driver.get(URL)
        time.sleep(1)

    def accept_cookies(self) -> webdriver.Chrome:
        print("Accepting cookies")
        self.navigate_to(self.URL)
        time.sleep(2)
        accept_cookies_button = self.driver.find_element_by_xpath(
            "//button[@id='banner-cookie-consent-allow-all']")
        accept_cookies_button.click()

    def retrieve_links_from_current_page(self):
        time.sleep(2)
        print("Retrieving links")
        products = self.driver.find_elements_by_xpath(
            "//*[@class='g4m-grid-product-listing']/a")
        page_list_of_product_urls = [
            product.get_attribute("href") for product in products]
        return page_list_of_product_urls

    def retrieve_links(self, number_of_pages=2):
        self.accept_cookies()
        print("Retrieving links.")
        list_of_product_urls = []
        for i in range(number_of_pages):
            url = self.URL + \
                "?page=" + str(i+1)
            self.navigate_to(url)
            list_of_product_urls.extend(
                self.retrieve_links_from_current_page())
        print(list_of_product_urls)
        self.list_of_product_urls = list_of_product_urls
        return list_of_product_urls

    def collect_data(self, url):
        print("Collecting data")
        data = {}
        time.sleep(1)
        self.navigate_to(url)
        product_ref = self.driver.find_element_by_xpath(
            "//p[@class='prd-ref']").text.split(":")[1]
        print("Product ref:", product_ref)
        product_uuid = uuid.uuid4()
        print("UUID:", product_uuid)
        # TODO retrieve data
        product_name = self.driver.find_element_by_xpath(
            "//h1[@itemprop='name']").text
        print("Name:", product_name)
        price = self.driver.find_element_by_xpath(
            "//span[@class='c-val']").text
        print("Price: £", price)
        # TODO deal with case where out of stock
        stock = self.driver.find_element_by_xpath(
            "//div[@class='tooltip-source info-row-stock-msg instock in-stock']").text.split()[0]
        print("Stock:", stock)
        description = self.driver.find_element_by_xpath(
            "//div[@class='slide']").text.split(":", 1)[1]
        print("Description:", description)
        main_image = self.driver.find_element_by_xpath(
            "//img[@class='main-image']"
        ).get_attribute("src")
        print("Image:", main_image)
        other_images_container = self.driver.find_elements_by_xpath(
            "//li[@class='image']/a"
        )
        other_images = [image.get_attribute(
            "href") for image in other_images_container]
        print(other_images)
        # check if it's flagged as a sale

        special_messages = self.driver.find_elements_by_xpath(
            "//div[@class='info-row-special-msg info-row-item']"
        )
        sale = False
        for message in special_messages:
            if message.text == "SALE":
                sale = True
        print("On sale:", sale)


# %%
if __name__ == "__main__":
    gear4music = scraper("https://www.gear4music.com/podcasting/microphones")
    gear4music.collect_data("https://www.gear4music.com/Recording-and-Computers/SZC-300-USB-Condenser-Microphone-with-Microphone-Arm/3RKW")
# %%

# %%
